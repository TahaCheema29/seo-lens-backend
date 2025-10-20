import asyncio
import urllib.robotparser
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from lxml import etree
from datetime import datetime
from enum import Enum
from logger_config import setup_logger


class URLStatus(Enum):
    SITEMAP = "From Sitemap"
    DISCOVERED = "Discovered by Crawl"
    BLOCKED = "Blocked by Robots"
    VISITED = "Visited"
    ERROR = "Error / Broken / Noindex"


class CrawlMode(Enum):
    SITEMAP_ONLY = 1
    FULL_CRAWL = 2


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/118.0.5993.88 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

SITEMAP_URLS = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"]


class SEOCrawler:
    def __init__(self, start_url: str, crawl_mode: CrawlMode = CrawlMode.SITEMAP_ONLY, max_workers: int = 5):
        self.start_url = start_url.rstrip("/")
        self.crawl_mode = crawl_mode
        self.max_workers = max_workers

        self.url_info: dict[str, URLStatus] = {}
        self.visited_links: set[str] = set()
        self.queue: asyncio.Queue | None = None
        self.lock: asyncio.Lock | None = None

        self.logger = setup_logger(__name__)


    @staticmethod
    def extract_links(html: str, base_url: str) -> set[str]:
        """Extract same-domain links from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()
            if not href or href.startswith("#") or href.startswith("/#"):
                continue
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.add(full_url)
        return links

    @staticmethod
    def is_allowed(url: str, disallowed_paths: list[str]) -> bool:
        """Check if URL path is allowed based on disallowed prefixes."""
        path = urlparse(url).path
        for disallowed in disallowed_paths:
            if path.startswith(disallowed):
                return False
        return True

    @staticmethod
    def get_robots_parser(base_url: str):
        robots_url = f"{base_url.rstrip('/')}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)

        allowed = set()
        disallowed = set()

        try:
            response = requests.get(robots_url, headers=HEADERS, timeout=5)
            if response.status_code == 200:
                lines = response.text.splitlines()
                rp.parse(lines)
                current_user_agent = None
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.lower().startswith("user-agent:"):
                        current_user_agent = line.split(":", 1)[1].strip()
                    elif line.lower().startswith("allow:") and current_user_agent in ("*", "seo-lens-bot"):
                        allowed.add(line.split(":", 1)[1].strip())
                    elif line.lower().startswith("disallow:") and current_user_agent in ("*", "seo-lens-bot"):
                        disallowed.add(line.split(":", 1)[1].strip())
            else:
                rp.parse([])
        except requests.RequestException:
            rp.parse([])
        return rp, allowed, disallowed

    @staticmethod
    def get_sitemap_urls_from_robots(base_url: str) -> set[str]:
        robots_url = f"{base_url.rstrip('/')}/robots.txt"
        sitemaps = set()
        try:
            response = requests.get(robots_url, headers=HEADERS, timeout=5)
            if response.status_code == 200:
                for line in response.text.splitlines():
                    if line.lower().startswith("sitemap:"):
                        sitemaps.add(line.split(":", 1)[1].strip())
        except requests.RequestException:
            pass

        # Try default paths if no sitemap found
        if not sitemaps:
            for path in SITEMAP_URLS:
                test_url = f"{base_url.rstrip('/')}{path}"
                try:
                    response = requests.head(test_url, timeout=5)
                    if response.status_code == 200:
                        sitemaps.add(test_url)
                except requests.RequestException:
                    continue
        return sitemaps

    async def get_urls_from_sitemap(self, sitemap_urls: str | set[str], visited=None) -> list[str]:
        """Recursively extract URLs from sitemap or sitemap index."""
        if visited is None:
            visited = set()
        urls = []

        if isinstance(sitemap_urls, str):
            sitemap_urls = [sitemap_urls]
        elif isinstance(sitemap_urls, set):
            sitemap_urls = list(sitemap_urls)

        for sitemap_url in sitemap_urls:
            try:
                response = requests.get(sitemap_url, headers=HEADERS, timeout=10)
                response.raise_for_status()
                content = response.content
            except Exception as e:
                print(f"[!] Requests failed for {sitemap_url}: {e} — retrying with Playwright...")
                try:
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=True)
                        page = await browser.new_page()
                        await page.goto(sitemap_url, timeout=10000)
                        content = await page.content()
                        await browser.close()
                except Exception as e2:
                    print(f"[!] Playwright also failed for {sitemap_url}: {e2}")
                    continue

            try:
                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(content.encode("utf-8") if isinstance(content, str) else content, parser)
                ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

                # Extract URLs
                for loc in root.xpath('//sm:url/sm:loc/text()', namespaces=ns):
                    urls.append(loc.strip())

                # Nested sitemaps
                for sub_sitemap in root.xpath('//sm:sitemap/sm:loc/text()', namespaces=ns):
                    sub_url = sub_sitemap.strip()
                    if sub_url not in visited:
                        visited.add(sub_url)
                        urls.extend(await self.get_urls_from_sitemap({sub_url}, visited))
            except Exception as e:
                print(f"[!] Error parsing sitemap {sitemap_url}: {e}")

        return urls


    async def crawl_page(self, page, url, disallowed_paths):
        """Visit a single page and extract internal links."""
        if url in self.visited_links:
            return

        if not self.is_allowed(url, disallowed_paths):
            self.url_info[url] = URLStatus.BLOCKED
            return

        async with self.lock:
            self.visited_links.add(url)
            self.url_info[url] = URLStatus.VISITED

        try:
            await page.goto(url, timeout=8000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(1000)
            print(f"🌍 Visiting: {url}")
        except Exception as e:
            self.url_info[url] = URLStatus.ERROR
            print(f"⚠️ Failed to load {url}: {e}")
            return

        html = await page.content()
        links = self.extract_links(html, self.start_url)

        for link in links:
            if link not in self.url_info:
                if self.is_allowed(link, disallowed_paths):
                    self.url_info[link] = URLStatus.DISCOVERED
                    async with self.lock:
                        try:
                            await self.queue.put(link)
                        except asyncio.QueueFull:
                            pass
                else:
                    self.url_info[link] = URLStatus.BLOCKED


    async def worker(self, browser, worker_id, disallowed_paths):
        page = await browser.new_page()
        consecutive_empty = 0
        while consecutive_empty < 3:
            try:
                url = await asyncio.wait_for(self.queue.get(), timeout=2)
                consecutive_empty = 0
            except asyncio.TimeoutError:
                consecutive_empty += 1
                continue
            try:
                await self.crawl_page(page, url, disallowed_paths)
            finally:
                self.queue.task_done()
        await page.close()
        print(f"Worker {worker_id} finished")


    async def run(self):
        crawl_start_time = datetime.now()
        print(f"🔹 Crawl START: {self.start_url} at {crawl_start_time}")

        rp, allowed_paths, disallowed_paths = self.get_robots_parser(self.start_url)
        sitemap_urls = self.get_sitemap_urls_from_robots(self.start_url)
        all_urls = await self.get_urls_from_sitemap(sitemap_urls)

        if self.crawl_mode == CrawlMode.FULL_CRAWL:
            self.queue = asyncio.Queue(maxsize=5000)
            self.lock = asyncio.Lock()

            for url in all_urls:
                if self.is_allowed(url, disallowed_paths):
                    self.url_info[url] = URLStatus.SITEMAP
                    await self.queue.put(url)
                else:
                    self.url_info[url] = URLStatus.BLOCKED

            if len(all_urls) == 0:
                if self.is_allowed(self.start_url, disallowed_paths):
                    self.url_info[self.start_url] = URLStatus.SITEMAP
                    await self.queue.put(self.start_url)

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                tasks = [self.worker(browser, i, disallowed_paths) for i in range(self.max_workers)]
                await asyncio.gather(*tasks)
                await browser.close()

        crawl_end_time = datetime.now()
        duration = crawl_end_time - crawl_start_time

        print("\n✅ Crawl complete")
        print(f"Total URLs tracked: {len(self.url_info) if self.crawl_mode == CrawlMode.FULL_CRAWL else len(all_urls)}")
        print(f"Started at: {crawl_start_time}")
        print(f"Ended at: {crawl_end_time}")
        print(f"Duration: {duration}")

        return self.url_info if self.crawl_mode == CrawlMode.FULL_CRAWL else all_urls


if __name__ == "__main__":
    crawler = SEOCrawler(
        start_url="https://cookieandkate.com/",
        crawl_mode=CrawlMode.SITEMAP_ONLY, 
        max_workers=5
    )
    asyncio.run(crawler.run())

    # start_url = "https://www.cachelogic.tech/"
    # start_url = "https://verdant-soft.com/"
    # start_url = "https://cookieandkate.com/"
    # start_url = "https://ahrefs.com/"