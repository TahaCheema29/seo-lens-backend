import asyncio
from datetime import datetime
import json
import requests
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from src.config.redis_client import redis_client
from src.config.settings import settings
from src.config.logger_config import setup_logger
from src.schemas.analyze_site_seo import AnalyzeSiteSeoResult

load_dotenv()
logger = setup_logger(__name__)


class SEOScraper:
    def __init__(self, start_url: str, max_workers: int = 5):
        self.start_url = start_url
        self.max_workers = max_workers
        self.results = []
        self.lock = asyncio.Lock()
        self.google_cloud_api_key_3 = settings.google_cloud_api_key_3
        self.logger = setup_logger(__name__)

    @staticmethod
    def extract_seo_tags(html, url):
        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        meta_description = (
            (soup.find("meta", attrs={"name": "description"}) or {})
            .get("content", "")
            .strip()
        )
        meta_keywords = (
            (soup.find("meta", attrs={"name": "keywords"}) or {})
            .get("content", "")
            .strip()
        )

        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
        h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

        h1 = (
            h1_tags[0]
            if len(h1_tags) == 1
            else f"{len(h1_tags)} H1 tags found: " + " | ".join(h1_tags)
            if h1_tags
            else "No H1"
        )

        img_tags = soup.find_all("img")
        bad_alt_keywords = {"image", "photo", "picture", "img", "logo"}
        missing_or_poor_alts = [
            img
            for img in img_tags
            if not img.get("alt")
            or img.get("alt", "").strip().lower() in bad_alt_keywords
        ]
        alt_check = (
            "✅ All images have descriptive alt attributes"
            if not missing_or_poor_alts
            else f"❌ {len(missing_or_poor_alts)} images missing/poor alt text"
        )

        canonical_tag = soup.find("link", rel="canonical")
        canonical = (
            canonical_tag["href"].strip()
            if canonical_tag and canonical_tag.get("href")
            else ""
        )

        viewport_tag = soup.find("meta", attrs={"name": "viewport"})
        mobile_responsiveness = (
            "✅ Viewport meta found"
            if viewport_tag and "width=device-width" in viewport_tag.get("content", "")
            else "❌ Missing or incorrect viewport tag"
        )

        schema_scripts = soup.find_all("script", type="application/ld+json")
        schema_types = []
        schema_validation = ""
        if schema_scripts:
            for s in schema_scripts:
                try:
                    data = json.loads(s.string)
                    types = [
                        item.get("@type")
                        for item in (data if isinstance(data, list) else [data])
                        if "@type" in item
                    ]
                    schema_types.extend(types)
                except:
                    schema_validation = "❌ Invalid JSON-LD format"
            schema_validation = schema_validation or (
                f"✅ Valid Schema Found: {', '.join(set(schema_types))}"
                if schema_types
                else "⚠️ No recognizable schema"
            )
        else:
            schema_validation = "❌ No structured data"

        return {
            "url": url,
            "title": title,
            "meta_description": meta_description,
            "meta_keywords": meta_keywords,
            "h1": h1,
            "h2": " | ".join(h2_tags),
            "h3": " | ".join(h3_tags),
            "alt_check": alt_check,
            "canonical": canonical,
            "mobile_responsiveness": mobile_responsiveness,
            "schema_validation": schema_validation,
        }

    async def check_core_web_vitals(self, url):
        """Fetch Core Web Vitals from PageSpeed API"""
        try:
            key = f"pagespeedresponse:{url}"
            r = await redis_client.get(key)
            if not r:
                r = requests.get(
                    "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                    params={
                        "url": url,
                        "key": self.google_cloud_api_key_3,
                        "category": "performance",
                    },
                    timeout=30,
                )
                ttl = 6 * 60 * 60
                await redis_client.setex(key, ttl, r)

            metrics = r.json()["loadingExperience"]["metrics"]
            lcp = metrics["LARGEST_CONTENTFUL_PAINT_MS"]["percentile"] / 1000
            fid = metrics["FIRST_INPUT_DELAY_MS"]["percentile"]
            cls = metrics["CUMULATIVE_LAYOUT_SHIFT_SCORE"]["percentile"] / 100

            return {"lcp": f"{lcp:.2f}s", "fid": f"{fid:.0f}ms", "cls": f"{cls:.2f}"}
        except Exception:
            return {"lcp": "-", "fid": "-", "cls": "-"}

    async def scrape_worker(self, browser, worker_id, queue: asyncio.Queue):
        page = await browser.new_page()
        while True:
            try:
                url = await asyncio.wait_for(queue.get(), timeout=2)
            except asyncio.TimeoutError:
                break
            try:
                await page.goto(url, timeout=10000)
                await page.wait_for_load_state("domcontentloaded")
                html = await page.content()
                data = self.extract_seo_tags(html, url)

                if self.google_cloud_api_key_3:
                    print("checking web vitals")
                    vitals = await self.check_core_web_vitals(url)
                    print("vitals are ", vitals)
                    data.update(vitals)

                async with self.lock:
                    self.results.append(data)

                print("result is ", self.results)

            except Exception as e:
                self.logger.error(f"Worker {worker_id} failed on {url}: {e}")
            finally:
                queue.task_done()

        await page.close()
        print("result is ", self.results)
        print(f"✅ Worker {worker_id} finished")

    async def run(self, urls):
        """Run scraping process for all URLs"""
        queue = asyncio.Queue()
        for url in urls:
            await queue.put(url)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            tasks = [
                self.scrape_worker(browser, i, queue) for i in range(self.max_workers)
            ]
            await asyncio.gather(*tasks)
            await browser.close()

        validated_results = [AnalyzeSiteSeoResult(**res) for res in self.results]
        return validated_results

    def save_to_html(self, filename="seo_results.html"):
        """Save scraped SEO results to a styled HTML file"""
        if not self.results:
            print("⚠️ No results to save")
            return

        # Define CSS styling
        style = """
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background-color: #f8fafc;
                    color: #1e293b;
                    padding: 30px;
                }
                h1 {
                    text-align: center;
                    color: #0f172a;
                    margin-bottom: 20px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    border-radius: 8px;
                    overflow: hidden;
                }
                th, td {
                    border: 1px solid #e2e8f0;
                    text-align: left;
                    padding: 10px 15px;
                }
                th {
                    background-color: #1e3a8a;
                    color: white;
                    font-weight: 600;
                }
                tr:nth-child(even) {
                    background-color: #f1f5f9;
                }
                tr:hover {
                    background-color: #e2e8f0;
                }
                a {
                    color: #2563eb;
                    text-decoration: none;
                }
                a:hover {
                    text-decoration: underline;
                }
                .status-ok {
                    color: green;
                    font-weight: bold;
                }
                .status-bad {
                    color: red;
                    font-weight: bold;
                }
                footer {
                    text-align: center;
                    margin-top: 30px;
                    font-size: 0.9em;
                    color: #64748b;
                }
            </style>
            """

        # Build HTML table
        html = [
            "<html><head><meta charset='UTF-8'><title>SEO Results</title>",
            style,
            "</head><body>",
        ]
        html.append("<h1>Verdant Soft – SEO Audit Results</h1>")
        html.append("<table><thead><tr>")

        # Add table headers
        for header in self.results[0].keys():
            html.append(f"<th>{header}</th>")
        html.append("</tr></thead><tbody>")

        # Add table rows
        for row in self.results:
            html.append("<tr>")
            for key, value in row.items():
                # Turn URLs into clickable links
                if key.lower() == "url":
                    cell = f"<a href='{value}' target='_blank'>{value}</a>"
                # Add green/red indicators for check columns
                elif "✅" in str(value):
                    cell = f"<span class='status-ok'>{value}</span>"
                elif "❌" in str(value):
                    cell = f"<span class='status-bad'>{value}</span>"
                else:
                    cell = value or ""
                html.append(f"<td>{cell}</td>")
            html.append("</tr>")
        html.append("</tbody></table>")

        # Footer with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html.append(f"<footer>Generated on {timestamp}</footer>")
        html.append("</body></html>")

        # Write HTML file
        with open(filename, "w", encoding="utf-8") as f:
            f.write("".join(html))

        print(f"📄 SEO results saved to {filename}")
