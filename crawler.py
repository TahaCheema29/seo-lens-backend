import asyncio
import time
import csv
from logger_config import setup_logger
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = setup_logger(__name__)
visited_links = set()
queue = None
lock = None
results = []

def extract_links(html, base_url):
    """Extract same-domain <a> links from HTML."""
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


async def crawl_page(page, url, start_url):
    """Visit a page, extract links, and enqueue new links."""
    async with lock:
        if url in visited_links:
            return
        visited_links.add(url)

    try:
        await page.goto(url, timeout=15000)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(500)
        print(f"🌍 Visiting: {url}")
    except Exception as e:
        print(f"⚠️ Failed to load {url}: {e}")
        return

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
    """Worker task to collect all internal links."""
    page = await browser.new_page()
    consecutive_empty = 0
    max_consecutive_empty = 3

    while consecutive_empty < max_consecutive_empty:
        try:
            url = await asyncio.wait_for(queue.get(), timeout=2)
            consecutive_empty = 0
        except asyncio.TimeoutError:
            consecutive_empty += 1
            if queue.qsize() == 0:
                await asyncio.sleep(1)
            continue

        try:
            await crawl_page(page, url, start_url)
        except Exception as e:
            logger.error(f"Worker {worker_id} failed on {url}: {e}")
        finally:
            queue.task_done()

    await page.close()
    print(f"Worker {worker_id} finished")


#helper functions for scrapping
def scrape_seo_tags(html, url):
    """Extract SEO-relevant tags from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title else ""

    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    meta_keywords = ""
    keywords_tag = soup.find("meta", attrs={"name": "keywords"})
    if keywords_tag and keywords_tag.get("content"):
        meta_keywords = keywords_tag["content"].strip()

    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

    h1_info = h1_tags[0] if len(h1_tags) == 1 else f"{len(h1_tags)} H1 tags: {' | '.join(h1_tags)}"

    img_tags = soup.find_all("img")
    img_alts = [img.get("alt", "").strip() for img in img_tags]
    missing_alts = [img.get("src", "") for img in img_tags if not img.get("alt")]

    alt_status = "✅ All images have alt text" if not missing_alts else f"❌ {len(missing_alts)} missing alts"

    canonical_tag = soup.find("link", rel="canonical")
    canonical_url = canonical_tag["href"].strip() if canonical_tag and canonical_tag.get("href") else ""

    return {
        "URL": url,
        "Title": title,
        "Meta Description": meta_desc,
        "Meta Keywords": meta_keywords,
        "H1": h1_info,
        "H2": " | ".join(h2_tags),
        "H3": " | ".join(h3_tags),
        "Alt Check": alt_status,
        "Canonical": canonical_url,
    }


async def scrape_all_pages(browser):
    """Go through all collected URLs and scrape SEO tags."""
    page = await browser.new_page()
    for idx, url in enumerate(visited_links):
        try:
            print(f"🔍 Scraping SEO data ({idx+1}/{len(visited_links)}): {url}")
            await page.goto(url, timeout=15000)
            await page.wait_for_load_state("domcontentloaded")
            html = await page.content()
            data = scrape_seo_tags(html, url)
            results.append(data)
        except Exception as e:
            print(f"⚠️ Failed to scrape {url}: {e}")
    await page.close()



async def main():
    global queue, lock
    start_url = "https://verdantsoft.com/"

    queue = asyncio.Queue(maxsize=1000)
    lock = asyncio.Lock()
    await queue.put(start_url)

    start_time = time.perf_counter()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        print("\n===== CRAWLING LINKS =====")
        tasks = [worker(browser, start_url, i) for i in range(5)]
        await asyncio.gather(*tasks)

        print(f"\n✅ Total internal links collected: {len(visited_links)}")

        print("\n===== SCRAPING SEO TAGS =====")
        await scrape_all_pages(browser)

        await browser.close()

    # Save results
    with open("seo_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "URL", "Title", "Meta Description", "Meta Keywords",
            "H1", "H2", "H3", "Alt Check", "Canonical"
        ])
        writer.writeheader()
        writer.writerows(results)

    end_time = time.perf_counter()
    print(f"\n SEO data saved to seo_results.csv")
    print(f"\n Total execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
