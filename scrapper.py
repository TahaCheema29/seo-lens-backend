import asyncio
import urllib.robotparser
from logger_config import setup_logger
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from lxml import etree
from datetime import datetime

from enum import Enum

class URLStatus(Enum):
    SITEMAP = "From Sitemap"
    DISCOVERED = "Discovered by Crawl"
    BLOCKED = "Blocked by Robots"
    VISITED = "Visited"
    ERROR = "Error / Broken / Noindex"

# Global tracking dictionary
url_info: dict[str, URLStatus] = {}

logger = setup_logger(__name__)
visited_links = set()
queue = None
lock = None  


def extract_links(html, base_url):
    """Extract same-domain <a> links from HTML, skip section anchors like /#..."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href:
            continue
        if href.startswith("#") or href.startswith("/#"):
            continue
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            links.add(full_url)
    return links


async def crawl_page(page, url, start_url, disallowed_paths):
    """Visit a page, extract links, and queue new ones"""
    global visited_links, queue, url_info

    if url in visited_links:
        return

    # Respect robots.txt
    if not is_allowed(url, disallowed_paths):
        url_info[url] = URLStatus.BLOCKED
        return

    async with lock:
        visited_links.add(url)
        url_info[url] = URLStatus.VISITED

    try:
        await page.goto(url, timeout=8000)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(1000)
        print(f"🌍 Visiting: {url}")
    except Exception as e:
        url_info[url] = URLStatus.ERROR
        print(f"⚠️ Failed to load {url}: {e}")
        return

    # Extract internal links
    html = await page.content()
    links = extract_links(html, start_url)

    for link in links:
        if link not in url_info:
            # Check robots.txt
            if is_allowed(link, disallowed_paths):
                url_info[link] = URLStatus.DISCOVERED
                async with lock:
                    try:
                        await queue.put(link)
                    except asyncio.QueueFull:
                        pass
            else:
                url_info[link] = URLStatus.BLOCKED


async def worker(browser, start_url, worker_id, disallowed_paths):
    page = await browser.new_page()
    consecutive_empty = 0
    max_consecutive_empty = 3

    while consecutive_empty < max_consecutive_empty:
        try:
            url = await asyncio.wait_for(queue.get(), timeout=2)
            print("url is ",url)
            consecutive_empty = 0
        except asyncio.TimeoutError:
            consecutive_empty += 1
            if queue.qsize() == 0:
                await asyncio.sleep(1)
                continue
            else:
                continue

        try:
            await crawl_page(page, url, start_url, disallowed_paths)
        finally:
            queue.task_done()

    await page.close()
    print(f"Worker {worker_id} finished")


def get_robots_parser(base_url: str):
    
    robots_url = f"{base_url.rstrip('/')}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    allowed = set()
    disallowed = set()

    try:
        response = requests.get(robots_url, timeout=5)
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
                    path = line.split(":", 1)[1].strip()
                    allowed.add(path)

                elif line.lower().startswith("disallow:") and current_user_agent in ("*", "seo-lens-bot"):
                    path = line.split(":", 1)[1].strip()
                    disallowed.add(path)

        else:
            print(f"[!] robots.txt not found or inaccessible at {robots_url}")
            rp.parse([])

    except requests.RequestException as e:
        print(f"[!] Error fetching robots.txt: {e}")
        rp.parse([])

    return rp, allowed, disallowed


def get_sitemap_urls_from_robots(base_url:str)-> set():
    
    robots_url=f"{base_url.rstrip("/")}/robots.txt"
    sitemaps=set()

    try:
        response=requests.get(robots_url,timeout=5)
        if response.status_code==200:
            for line in response.text.splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemaps.add(line.split(":",1),[1].strip())
    except requests.RequestException:
        pass #Ignore for now

    if not sitemaps:
        for path in ["/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"]:
            test_url=f"{base_url.rstrip("/")}{path}"

            try:
                response=requests.head(test_url,timeout=5)
                if response.status_code==200:
                    sitemaps.add(test_url)
            except requests.RequestException:
                continue

    return sitemaps
    

def get_urls_from_sitemap(sitemap_urls: str | set[str], visited=None)-> list[str]:

    if visited is None:
        visited = set()

    urls = []
    
    # Normalize input (can be str, set, list)
    if isinstance(sitemap_urls, str):
        sitemap_urls = [sitemap_urls]
    elif isinstance(sitemap_urls, set):
        sitemap_urls = list(sitemap_urls)
        
    for sitemap_url in sitemap_urls:
        
        try:
            response = requests.get(sitemap_url, timeout=5)
            response.raise_for_status()

            parser = etree.XMLParser(recover=True)
            root = etree.fromstring(response.content, parser)

            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            # --- Case 1: Regular URLs ---
            for loc in root.xpath('//sm:url/sm:loc/text()', namespaces=ns):
                urls.append(loc.strip())

            # --- Case 2: Sitemap Index (nested sitemaps) ---
            for sub_sitemap in root.xpath('//sm:sitemap/sm:loc/text()', namespaces=ns):
                sub_url = sub_sitemap.strip()
                if sub_url not in visited:
                    visited.add(sub_url)
                    urls.extend(get_urls_from_sitemap({sub_url}, visited))

        except Exception as e:
            print(f"[!] Error reading {sitemap_url}: {e}")

    return urls


def is_allowed(url: str, disallowed_paths: list[str]) -> bool:
  
    parsed_url = urlparse(url)
    path = parsed_url.path

    for disallowed in disallowed_paths:
        # Match disallowed prefixes (like '/private' should block '/private/page')
        if path.startswith(disallowed):
            return False
    return True


def filter_allowed_urls(urls: list[str], disallowed_paths: list[str]) -> list[str]:
   
    allowed = []
    for url in urls:
        if is_allowed(url, disallowed_paths):
            allowed.append(url)
    return allowed

# start_url = "https://verdant-soft.com/"
# start_url = "https://quotes.toscrape.com/"
# start_url = "https://cookieandkate.com/"
# start_url = "https://ahrefs.com/"
# start_url = "https://www.cachelogic.tech/"


async def main():
    global queue, lock, visited_links, url_info
    start_url = "https://www.cachelogic.tech/"

    # Record start time
    crawl_start_time = datetime.now()
    logger.info(f"🔹 Crawl START: {start_url} at {crawl_start_time}")
    print(f"🔹 Crawl START: {start_url} at {crawl_start_time}")

    # Parse robots.txt
    rp, allowed_paths, disallowed_paths = get_robots_parser(start_url)

    # Get sitemap URLs and URLs from sitemap
    sitemap_urls = get_sitemap_urls_from_robots(start_url)
    all_urls = get_urls_from_sitemap(sitemap_urls)

    # Initialize async queue and lock
    queue = asyncio.Queue(maxsize=5000)
    lock = asyncio.Lock()

    # Enqueue sitemap URLs, respecting robots.txt
    for url in all_urls:
        if is_allowed(url, disallowed_paths):
            url_info[url] = URLStatus.SITEMAP
            await queue.put(url)
        else:
            url_info[url] = URLStatus.BLOCKED

    if len(all_urls) == 0:
        if is_allowed(start_url, disallowed_paths):
            url_info[start_url] = URLStatus.SITEMAP
            await queue.put(start_url)

    # Crawl pages with Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        num_workers = 5
        tasks = [worker(browser, start_url, i, disallowed_paths) for i in range(num_workers)]
        await asyncio.gather(*tasks)
        await browser.close()

    # Log crawl summary
    crawl_end_time = datetime.now()
    duration = crawl_end_time - crawl_start_time

    logger.info("\n✅ Crawl complete")
    logger.info(f"Total URLs tracked: {len(url_info)}")
    logger.info(f"Crawl started at: {crawl_start_time}")
    logger.info(f"Crawl ended at: {crawl_end_time}")
    logger.info(f"Total duration: {duration}")

    print("\n✅ Crawl complete")
    print(f"Total URLs tracked: {len(url_info)}")
    print(f"Crawl started at: {crawl_start_time}")
    print(f"Crawl ended at: {crawl_end_time}")
    print(f"Total duration: {duration}")

    logger.info(f"🔹 Crawl END: {start_url}")
    print(f"🔹 Crawl END: {start_url}")

if __name__ == "__main__":
    asyncio.run(main())
