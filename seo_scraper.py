import asyncio
import csv
import json
import os
import requests
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from logger_config import setup_logger

load_dotenv()
# logger = setup_logger(__name__)

class SEOScraper:
    def __init__(self, start_url: str, max_workers: int = 5):
        self.start_url = start_url
        self.max_workers = max_workers
        self.results = []
        self.lock = asyncio.Lock()
        self.api_key = os.getenv("PAGESPEED_API_KEY")
        # self.logger = setup_logger(__name__)

    @staticmethod
    def extract_seo_tags(html, url):
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
        missing_or_poor_alts = [img for img in img_tags if not img.get("alt") or img.get("alt", "").strip().lower() in bad_alt_keywords]
        alt_status = "✅ All images have descriptive alt attributes" if not missing_or_poor_alts else f"❌ {len(missing_or_poor_alts)} images missing/poor alt text"

        canonical_tag = soup.find("link", rel="canonical")
        canonical_url = canonical_tag["href"].strip() if canonical_tag and canonical_tag.get("href") else ""

        viewport_tag = soup.find("meta", attrs={"name": "viewport"})
        responsive_status = "✅ Viewport meta found" if viewport_tag and "width=device-width" in viewport_tag.get("content", "") else "❌ Missing or incorrect viewport tag"

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
                    schema_status = "❌ Invalid JSON-LD format"
            schema_status = schema_status or (f"✅ Valid Schema Found: {', '.join(set(schema_types))}" if schema_types else "⚠️ No recognizable schema")
        else:
            schema_status = "❌ No structured data"

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
            "Mobile Responsiveness": responsive_status,
            "Schema Validation": schema_status
        }

    def check_core_web_vitals(self, url):
        """Fetch Core Web Vitals from PageSpeed API"""
        try:
            r = requests.get(
                "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                params={"url": url, "key": self.api_key, "category": "performance"},
                timeout=30
            )
            metrics = r.json()["loadingExperience"]["metrics"]
            lcp = metrics["LARGEST_CONTENTFUL_PAINT_MS"]["percentile"] / 1000
            fid = metrics["FIRST_INPUT_DELAY_MS"]["percentile"]
            cls = metrics["CUMULATIVE_LAYOUT_SHIFT_SCORE"]["percentile"] / 100

            return {
                "LCP": f"{lcp:.2f}s",
                "FID": f"{fid:.0f}ms",
                "CLS": f"{cls:.2f}"
            }
        except Exception:
            return {"LCP": "-", "FID": "-", "CLS": "-"}

    async def scrape_worker(self, browser, worker_id, queue: asyncio.Queue):
        page = await browser.new_page()
        while True:
            try:
                url = await asyncio.wait_for(queue.get(), timeout=2)
            except asyncio.TimeoutError:
                break
            try:
                print(f"🔍 [Worker {worker_id}] Scraping {url}")
                await page.goto(url, timeout=10000)
                await page.wait_for_load_state("domcontentloaded")
                html = await page.content()
                data = self.extract_seo_tags(html, url)

                if self.api_key:
                    vitals = self.check_core_web_vitals(url)
                    data.update(vitals)

                async with self.lock:
                    self.results.append(data)

            except Exception as e:
                self.logger.error(f"Worker {worker_id} failed on {url}: {e}")
            finally:
                queue.task_done()

        await page.close()
        print(f"✅ Worker {worker_id} finished")

    async def run(self, urls):
        """Run scraping process for all URLs"""
        queue = asyncio.Queue()
        for url in urls:
            await queue.put(url)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            tasks = [self.scrape_worker(browser, i, queue) for i in range(self.max_workers)]
            await asyncio.gather(*tasks)
            await browser.close()

        return self.results

    def save_to_csv(self, filename="seo_results.csv"):
        """Save scraped results to CSV"""
        if not self.results:
            print("⚠️ No results to save")
            return

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
            writer.writeheader()
            writer.writerows(self.results)

        print(f"📁 Saved SEO data to {filename}")
