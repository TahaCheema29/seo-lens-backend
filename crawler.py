import asyncio
import time
import csv
import json
import requests
import aiohttp
from logger_config import setup_logger
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()
logger = setup_logger(__name__)
visited_links = set()
queue = None
lock = None
results = []


def extract_links(html, base_url):
    """Extract same-domain <a> links from HTML, skip section anchors like /#..."""
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


def scrape_seo_tags(html, url):
    """Extract SEO-relevant tags from HTML"""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc = (soup.find("meta", attrs={"name": "description"}) or {}).get("content", "").strip()
    meta_keywords = (soup.find("meta", attrs={"name": "keywords"}) or {}).get("content", "").strip()

    h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
    h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

    h1_info = h1_tags[0] if len(h1_tags) == 1 else f"{len(h1_tags)} H1 tags found: " + " | ".join(h1_tags) if h1_tags else "No H1"

    img_tags = soup.find_all("img")
    bad_alt_keywords = {"image", "photo", "picture", "img", "logo"}
    missing_or_poor_alts = []
    for img in img_tags:
        if not img.get("alt") or img.get("alt", "").strip().lower() in bad_alt_keywords:
            missing_or_poor_alts.append(img)
    
    if not missing_or_poor_alts:
        alt_status = "✅ All images have descriptive alt attributes"
    else:
        alt_status = f"❌ {len(missing_or_poor_alts)} images missing or with poor alt text"

    canonical_tag = soup.find("link", rel="canonical")
    if canonical_tag and canonical_tag.get("href"):
        canonical_url = canonical_tag["href"].strip()
    else:
        canonical_url = ""

    viewport_tag = soup.find("meta", attrs={"name": "viewport"})
    if viewport_tag and "width=device-width" in viewport_tag.get("content", ""):
        responsive_status = "✅ Viewport meta found"
    else:
        responsive_status = "❌ Missing or incorrect viewport tag"

    schema_scripts = soup.find_all("script", type="application/ld+json")
    schema_types = []
    schema_status = ""
    if schema_scripts:
        for s in schema_scripts:
            try:
                data = json.loads(s.string)
                types = [item.get("@type") for item in (data if isinstance(data, list) else [data]) if "@type" in item]
                schema_types.extend(types)
            except:
                schema_status = "❌ Invalid JSON-LD format detected"
        schema_status = schema_status or (f"✅ Valid Schema Found: {', '.join(set(schema_types))}" if schema_types else "⚠️ No recognizable schema types found")
    else:
        schema_status = "❌ No structured data detected"

    img_alts = " | ".join([img.get("alt", "").strip() for img in img_tags if img.get("alt")])

    return {
        "URL": url, "Title": title, "Meta Description": meta_desc, "Meta Keywords": meta_keywords,
        "H1": h1_info, "H2": " | ".join(h2_tags), "H3": " | ".join(h3_tags),
        "Image Alts": img_alts, "Alt Check": alt_status, "Canonical": canonical_url,
        "Mobile Responsiveness": responsive_status, "Schema Validation": schema_status
    }


def check_core_web_vitals(url, api_key):
    """Fetch Core Web Vitals metrics using Google PageSpeed Insights API"""
    try:
        response = requests.get("https://www.googleapis.com/pagespeedonline/v5/runPagespeed", 
                                params={"url": url, "key": api_key, "category": "performance"}, timeout=30)
        metrics = response.json()["loadingExperience"]["metrics"]
        lcp = metrics["LARGEST_CONTENTFUL_PAINT_MS"]["percentile"] / 1000
        fid = metrics["FIRST_INPUT_DELAY_MS"]["percentile"]
        cls = metrics["CUMULATIVE_LAYOUT_SHIFT_SCORE"]["percentile"] / 100

        return {
            "LCP": f"{lcp:.2f}s ({'Good' if lcp <= 2.5 else 'Needs Improvement' if lcp <= 4.0 else 'Poor'})",
            "FID": f"{fid:.0f}ms ({'Good' if fid <= 100 else 'Needs Improvement' if fid <= 300 else 'Poor'})",
            "CLS": f"{cls:.2f} ({'Good' if cls <= 0.1 else 'Needs Improvement' if cls <= 0.25 else 'Poor'})"
        }
    except:
        return {"error": "Core Web Vitals data not found"}


async def check_indexability(start_url):
    """Check robots.txt and sitemap.xml presence"""
    parsed = urlparse(start_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    results = {"Robots.txt": "❌ Missing", "Sitemap.xml": "❌ Missing"}

    async with aiohttp.ClientSession() as session:
        for file, key in [("/robots.txt", "Robots.txt"), ("/sitemap.xml", "Sitemap.xml")]:
            try:
                async with session.get(urljoin(base, file), timeout=10) as resp:
                    if resp.status == 200:
                        results[key] = "✅ Found"
            except:
                pass
    return results


async def crawl_page(page, url, start_url):
    """Visit a page and extract links only (no scraping yet)."""
    async with lock:
        if url in visited_links:
            return
        visited_links.add(url)

    try:
        await page.goto(url, timeout=20000)
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(1000)
        print(f"🌍 Crawling: {url}")
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
    """Worker to crawl pages and collect URLs only."""
    page = await browser.new_page()
    consecutive_empty = 0

    while consecutive_empty < 3:
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
    print(f"✅ Worker {worker_id} finished")


async def scrape_worker(browser, worker_id, scrape_queue):
    """Worker to scrape SEO data from URLs in parallel."""
    page = await browser.new_page()
    api_key = os.getenv("PAGESPEED_API_KEY")
    
    while True:
        try:
            url = await asyncio.wait_for(scrape_queue.get(), timeout=2)
        except asyncio.TimeoutError:
            break
        
        try:
            print(f"🔍 Worker {worker_id} scraping: {url}")
            await page.goto(url, timeout=20000)
            await page.wait_for_load_state("domcontentloaded")
            html = await page.content()
            seo_data = scrape_seo_tags(html, url)

            if api_key:
                for attempt in range(3):
                    vitals = check_core_web_vitals(url, api_key)
                    if "error" not in vitals:
                        seo_data.update({"LCP (s)": vitals["LCP"], "FID (ms)": vitals["FID"], "CLS": vitals["CLS"]})
                        print(f"✅ Worker {worker_id}: Core Web Vitals fetched")
                        break
                    elif attempt == 2:
                        seo_data.update({"LCP (s)": vitals["error"], "FID (ms)": vitals["error"], "CLS": vitals["error"]})
                    else:
                        await asyncio.sleep(1)

            async with lock:
                results.append(seo_data)
            
        except Exception as e:
            print(f"⚠️ Worker {worker_id} failed to scrape {url}: {e}")
            logger.error(f"Scraping error for {url}: {e}")
        finally:
            scrape_queue.task_done()
    
    await page.close()
    print(f"✅ Scrape Worker {worker_id} finished")


async def main():
    global queue, lock
    start_url = "https://verdant-soft.com/"

    queue = asyncio.Queue(maxsize=1000)
    lock = asyncio.Lock()
    await queue.put(start_url)

    start_time = time.perf_counter()
    indexability = await check_indexability(start_url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        print("\n===== PHASE 1: CRAWLING LINKS =====")
        await asyncio.gather(*[worker(browser, start_url, i) for i in range(5)])
        print(f"\n✅ Total unique links collected: {len(visited_links)}")
        
        print("\n===== PHASE 2: SCRAPING SEO DATA =====")
        scrape_queue = asyncio.Queue()
        for url in visited_links:
            await scrape_queue.put(url)
        
        num_scrape_workers = 3
        scrape_tasks = [scrape_worker(browser, i, scrape_queue) for i in range(num_scrape_workers)]
        await asyncio.gather(*scrape_tasks)
        
        await browser.close()

    for row in results:
        row.update(indexability)

    with open("seo_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "URL", "Title", "Meta Description", "Meta Keywords", "H1", "H2", "H3", 
            "Image Alts", "Alt Check", "Canonical", "Mobile Responsiveness", "Schema Validation",
            "LCP (s)", "FID (ms)", "CLS", "Robots.txt", "Sitemap.xml"
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n⏱️ Total execution time: {time.perf_counter() - start_time:.2f} seconds")
    print("📁 SEO data saved to seo_results.csv")


if __name__ == "__main__":
    asyncio.run(main())