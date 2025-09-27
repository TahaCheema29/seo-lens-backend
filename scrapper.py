import asyncio
import time
from logger_config import setup_logger
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

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


async def crawl_page(page, url, start_url):
    """Visit a page, extract links, and enqueue new links."""
    async with lock:
        if url in visited_links:
            return
        visited_links.add(url)

    try:
        await page.goto(url, timeout=8000)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(1000)
        print(f"🌍 Visiting: {url}")
    except Exception as e:
        print(f"⚠️ Failed to load {url}: {e}")
        return

    # Step 1: Collect <a> links
    html = await page.content()
    links = extract_links(html, start_url)

    for link in links:
        async with lock:
            if link not in visited_links:
                try:
                    queue.put_nowait(link)
                except asyncio.QueueFull:
                    pass


async def worker(browser, start_url, worker_id):
    page = await browser.new_page()
    consecutive_empty = 0
    max_consecutive_empty = 3

    while consecutive_empty < max_consecutive_empty:
        try:
            url = await asyncio.wait_for(queue.get(), timeout=2)
            consecutive_empty = 0
        except asyncio.TimeoutError:
            consecutive_empty += 1
            async with lock:
                queue_size = queue.qsize()
            if queue_size == 0:
                await asyncio.sleep(1)
                continue
            else:
                continue

        try:
            await crawl_page(page, url, start_url)
        except Exception as e:
            logger.error(f"Worker {worker_id} failed on {url}: {e}")
        finally:
            queue.task_done()

    await page.close()
    print(f"Worker {worker_id} finished")


async def main():
    global queue, lock

    # start_url = "https://verdant-soft.com/"
    # start_url = "https://quotes.toscrape.com/"
    # start_url = "https://www.cachelogic.tech/"
    start_url = "https://cookieandkate.com/"
    # start_url = "https://ahrefs.com/"

    queue = asyncio.Queue(maxsize=1000)
    lock = asyncio.Lock()

    await queue.put(start_url)

    start_time = time.perf_counter()  

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        num_workers = 5
        tasks = [worker(browser, start_url, i) for i in range(num_workers)]

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"Error in workers: {e}")

        await browser.close()

    end_time = time.perf_counter()  
    total_time = end_time - start_time

    print(f"\n✅ Total unique links visited: {len(visited_links)}")
    print(f"⏱️ Total crawl time: {total_time:.2f} seconds")
    for link in sorted(visited_links):
        print(link)


if __name__ == "__main__":
    asyncio.run(main())
