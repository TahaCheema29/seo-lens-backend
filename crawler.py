import asyncio
import time
import csv
import aiohttp
from logger_config import setup_logger
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = setup_logger(__name__)
visited_links = set()
queue = None
lock = None
results = []  # store scraped data


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


def scrape_seo_tags(html, url):
    """Extract SEO-relevant tags from HTML"""
    soup = BeautifulSoup(html, "html.parser")

    # Meta & Title
    title = soup.title.string.strip() if soup.title else ""

    meta_desc = ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag and desc_tag.get("content"):
        meta_desc = desc_tag["content"].strip()

    meta_keywords = ""
    keywords_tag = soup.find("meta", attrs={"name": "keywords"})
    if keywords_tag and keywords_tag.get("content"):
        meta_keywords = keywords_tag["content"].strip()

    # Headings
    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

    if len(h1_tags) == 1:
        h1_info = h1_tags[0]
    else:
        h1_info = f"{len(h1_tags)} H1 tags found: " + " | ".join(h1_tags)

    # Images (alt attributes)
    img_tags = soup.find_all("img")
    img_alts = [img.get("alt", "").strip() for img in img_tags]

    bad_alt_keywords = {"image", "photo", "picture", "img", "logo"}
    missing_or_poor_alts = [
        (img.get("src", ""), img.get("alt", "").strip())
        for img in img_tags
        if not img.get("alt")
        or img.get("alt", "").strip().lower() in bad_alt_keywords
    ]

    if missing_or_poor_alts:
        alt_status = f"❌ {len(missing_or_poor_alts)} images missing or with poor alt text"
    else:
        alt_status = "✅ All images have descriptive alt attributes"

    # === canonical check ===
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
        "Image Alts": " | ".join([alt for alt in img_alts if alt]),
        "Alt Check": alt_status,
        "Canonical": canonical_url,
    }


async def check_indexability(start_url):
    """Check robots.txt and sitemap.xml presence"""
    parsed = urlparse(start_url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    results = {
        "Robots.txt": "❌ Missing",
        "Sitemap.xml": "❌ Missing",
    }

    async with aiohttp.ClientSession() as session:
        # robots.txt
        try:
            async with session.get(urljoin(base, "/robots.txt"), timeout=10) as resp:
                if resp.status == 200:
                    results["Robots.txt"] = "✅ Found"
        except:
            pass

        # sitemap.xml
        try:
            async with session.get(urljoin(base, "/sitemap.xml"), timeout=10) as resp:
                if resp.status == 200:
                    results["Sitemap.xml"] = "✅ Found"
        except:
            pass

    return results


async def crawl_page(page, url, start_url):
    """Visit a page, extract links, scrape SEO tags, and enqueue new links."""
    async with lock:
        if url in visited_links:
            return
        visited_links.add(url)

    try:
        await page.goto(url, timeout=20000)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(1000)
        print(f"🌍 Visiting: {url}")
    except Exception as e:
        print(f"⚠️ Failed to load {url}: {e}")
        return

    html = await page.content()
    seo_data = scrape_seo_tags(html, url)

    async with lock:
        results.append(seo_data)

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

    start_url = "https://verdant-soft.com/"
    queue = asyncio.Queue(maxsize=1000)
    lock = asyncio.Lock()
    await queue.put(start_url)

    start_time = time.perf_counter()

    # === indexability checks ===
    indexability = await check_indexability(start_url)

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

    # merge indexability results into each row
    for row in results:
        row.update(indexability)

    with open("seo_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "URL", "Title", "Meta Description", "Meta Keywords",
            "H1", "H2", "H3", "Image Alts", "Alt Check", "Canonical",
            "Robots.txt", "Sitemap.xml"
        ])
        writer.writeheader()
        writer.writerows(results)

    print("📁 SEO data saved to seo_results.csv")


if __name__ == "__main__":
    asyncio.run(main())
