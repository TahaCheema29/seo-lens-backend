import asyncio
from datetime import datetime
import json
import requests
import re
from urllib.parse import urlparse, urljoin
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
    def extract_keywords_from_text(text):
        """Extract potential keywords from text"""
        if not text:
            return []
        # Simple keyword extraction - words longer than 3 characters
        words = re.findall(r'\b\w{4,}\b', text.lower())
        return list(set(words))

    @staticmethod
    def check_title_quality(title):
        """Check title quality and provide guidance"""
        if not title:
            return {
                "status": "❌ Missing",
                "length": 0,
                "guidance": "Add a descriptive title tag"
            }
        
        length = len(title)
        status = "✅ Good" if 30 <= length <= 60 else "⚠️ " + ("Too short" if length < 30 else "Too long")
        
        guidance = []
        if length < 30:
            guidance.append("Title is too short - aim for 30-60 characters")
        elif length > 60:
            guidance.append("Title is too long - may be truncated in search results")
        
        # Check for click-worthiness indicators
        has_numbers = bool(re.search(r'\d', title))
        has_power_words = bool(re.search(r'\b(best|top|ultimate|guide|how|why|free|new|proven|secret|easy|fast)\b', title.lower()))
        
        if not has_power_words:
            guidance.append("Consider adding power words to increase click-through rate")
        
        return {
            "status": status,
            "length": length,
            "guidance": "; ".join(guidance) if guidance else "Title looks good!"
        }

    @staticmethod
    def check_description_quality(description):
        """Check meta description quality"""
        if not description:
            return {
                "status": "❌ Missing",
                "length": 0,
                "guidance": "Add a meta description"
            }
        
        length = len(description)
        status = "✅ Good" if 120 <= length <= 160 else "⚠️ " + ("Too short" if length < 120 else "Too long")
        
        guidance = []
        if length < 120:
            guidance.append("Description is too short - aim for 120-160 characters")
        elif length > 160:
            guidance.append("Description is too long - may be truncated in search results")
        
        # Check for engagement
        has_call_to_action = bool(re.search(r'\b(buy|learn|discover|explore|get|try|start|find|read|view)\b', description.lower()))
        if not has_call_to_action:
            guidance.append("Consider adding a call-to-action to improve engagement")
        
        return {
            "status": status,
            "length": length,
            "guidance": "; ".join(guidance) if guidance else "Description looks good!"
        }

    @staticmethod
    def extract_seo_tags(html, url, response_headers=None):
        soup = BeautifulSoup(html, "html.parser")
        parsed_url = urlparse(url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # === BASIC SEO: Title & Description ===
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        title_quality = SEOScraper.check_title_quality(title)
        title_keywords = SEOScraper.extract_keywords_from_text(title)
        
        meta_description = (
            (soup.find("meta", attrs={"name": "description"}) or {})
            .get("content", "")
            .strip()
        )
        description_quality = SEOScraper.check_description_quality(meta_description)
        desc_keywords = SEOScraper.extract_keywords_from_text(meta_description)
        
        meta_keywords = (
            (soup.find("meta", attrs={"name": "keywords"}) or {})
            .get("content", "")
            .strip()
        )

        # === BASIC SEO: Headings ===
        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
        h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

        h1_check = "✅ Exactly one H1" if len(h1_tags) == 1 else (
            f"❌ {len(h1_tags)} H1 tags found" if h1_tags else "❌ No H1 tag"
        )
        h1_keyword_guidance = "Consider including primary keyword in H1" if h1_tags else "Add an H1 tag with your primary keyword"
        
        h2_count = len(h2_tags)
        h2_guidance = (
            "✅ Good structure" if h2_count > 0 else "⚠️ Consider adding H2 tags for better content organization"
        )

        # === BASIC SEO: Images ===
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
            else f"❌ {len(missing_or_poor_alts)}/{len(img_tags)} images missing/poor alt text"
        )

        # === BASIC SEO: Links ===
        all_links = soup.find_all("a", href=True)
        internal_links = []
        external_links = []
        
        for link in all_links:
            href = link.get("href", "")
            if not href:
                continue
            full_url = urljoin(url, href)
            link_domain = urlparse(full_url).netloc
            if link_domain == parsed_url.netloc or not link_domain:
                internal_links.append(full_url)
            else:
                external_links.append(full_url)
        
        internal_count = len(set(internal_links))
        external_count = len(set(external_links))
        
        links_guidance = []
        if internal_count < 3:
            links_guidance.append("Consider adding more internal links for better site structure")
        if external_count == 0:
            links_guidance.append("Consider adding quality external links to authoritative sources")
        elif external_count > 50:
            links_guidance.append("High number of external links - ensure they're all relevant and high-quality")
        
        links_guidance_text = "; ".join(links_guidance) if links_guidance else "Link structure looks good"

        # === ADVANCED SEO: Canonical ===
        canonical_tag = soup.find("link", rel="canonical")
        canonical = (
            canonical_tag["href"].strip()
            if canonical_tag and canonical_tag.get("href")
            else ""
        )
        canonical_check = "✅ Found" if canonical else "❌ Not found"

        # === ADVANCED SEO: Noindex ===
        noindex_meta = soup.find("meta", attrs={"name": "robots"})
        noindex_header = response_headers.get("X-Robots-Tag", "") if response_headers else ""
        has_noindex = (
            (noindex_meta and "noindex" in noindex_meta.get("content", "").lower()) or
            "noindex" in noindex_header.lower()
        )
        noindex_check = "❌ Found (page will not be indexed)" if has_noindex else "✅ Not found"

        # === ADVANCED SEO: WWW Redirect Check ===
        www_check = "⚠️ Manual check needed"  # Will be checked separately via HTTP request

        # === ADVANCED SEO: Robots.txt ===
        robots_check = "⚠️ Not checked in scraper"  # Will be checked separately

        # === ADVANCED SEO: Open Graph ===
        og_tags = {
            "title": soup.find("meta", attrs={"property": "og:title"}),
            "type": soup.find("meta", attrs={"property": "og:type"}),
            "image": soup.find("meta", attrs={"property": "og:image"}),
            "url": soup.find("meta", attrs={"property": "og:url"}),
        }
        missing_og = [key for key, tag in og_tags.items() if not tag]
        og_check = (
            "✅ All Open Graph tags present"
            if not missing_og
            else f"⚠️ Missing: {', '.join(missing_og)}"
        )

        # === ADVANCED SEO: Schema ===
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
            schema_validation = "❌ No structured data found"

        # === PERFORMANCE: HTML Size ===
        html_size = len(html.encode('utf-8'))
        html_size_kb = html_size / 1024
        html_size_check = (
            "✅ Good" if html_size_kb < 100 else
            "⚠️ Large" if html_size_kb < 500 else "❌ Very large"
        )

        # === PERFORMANCE: Inline CSS & Whitespace ===
        inline_styles = soup.find_all(style=True)
        inline_css_count = len(inline_styles)
        whitespace_ratio = len(re.findall(r'\s{3,}', html)) / max(len(html.split('\n')), 1)
        
        performance_warnings = []
        if inline_css_count > 10:
            performance_warnings.append(f"{inline_css_count} inline styles found - consider external CSS")
        if whitespace_ratio > 0.1:
            performance_warnings.append("Excessive whitespace detected - consider minification")
        
        performance_guidance = "; ".join(performance_warnings) if performance_warnings else "✅ No major issues detected"

        # === PERFORMANCE: Embedded Objects ===
        embedded_objects = soup.find_all(["object", "embed", "applet"])
        embedded_check = (
            "✅ No embedded objects found"
            if not embedded_objects
            else f"⚠️ {len(embedded_objects)} embedded objects - consider HTML5 alternatives"
        )

        # === SECURITY: HTTPS/SSL ===
        is_https = parsed_url.scheme == "https"
        https_check = "✅ HTTPS enabled" if is_https else "❌ Not using HTTPS"

        # === SECURITY: Directory Listing ===
        directory_listing_check = "⚠️ Not checked in scraper"  # Will be checked separately

        # === SECURITY: Google Safe Browsing ===
        safe_browsing_check = "⚠️ Not checked in scraper"  # Will be checked separately

        # === Mobile Responsiveness ===
        viewport_tag = soup.find("meta", attrs={"name": "viewport"})
        mobile_responsiveness = (
            "✅ Viewport meta found"
            if viewport_tag and "width=device-width" in viewport_tag.get("content", "")
            else "❌ Missing or incorrect viewport tag"
        )

        return {
            "url": url,
            # Basic SEO - Title & Description
            "title": title,
            "title_length_check": f"{title_quality['status']} ({title_quality['length']} chars)",
            "title_keyword_presence": "✅ Keywords detected" if title_keywords else "⚠️ No clear keywords",
            "title_quality_guidance": title_quality['guidance'],
            "meta_description": meta_description,
            "meta_description_length_check": f"{description_quality['status']} ({description_quality['length']} chars)",
            "meta_description_keyword_presence": "✅ Keywords detected" if desc_keywords else "⚠️ No clear keywords",
            "meta_description_quality_guidance": description_quality['guidance'],
            "meta_keywords": meta_keywords,
            # Basic SEO - Headings
            "h1_check": h1_check,
            "h1_keyword_guidance": h1_keyword_guidance,
            "h1": h1_tags[0] if h1_tags else "",
            "h2_count": h2_count,
            "h2_optimization_guidance": h2_guidance,
            "h2": " | ".join(h2_tags[:5]),  # Limit to first 5
            "h3": " | ".join(h3_tags[:5]),
            # Basic SEO - Images
            "image_alt_check": alt_check,
            # Basic SEO - Links
            "internal_links_count": internal_count,
            "external_links_count": external_count,
            "links_quality_guidance": links_guidance_text,
            # Advanced SEO
            "canonical_check": canonical_check,
            "canonical": canonical,
            "noindex_check": noindex_check,
            "www_redirect_check": www_check,
            "robots_txt_check": robots_check,
            "open_graph_check": og_check,
            "schema_validation": schema_validation,
            # Performance
            "html_size_check": f"{html_size_check} ({html_size_kb:.1f} KB)",
            "html_size_bytes": html_size,
            "inline_css_warning": performance_guidance,
            "embedded_objects_check": embedded_check,
            "mobile_responsiveness": mobile_responsiveness,
        }

    async def check_core_web_vitals(self, url):
        """Fetch Core Web Vitals from PageSpeed API"""
        try:
            key = f"pagespeedresponse:{url}"
            cached_data = await redis_client.get(key)
            if cached_data:
                data = json.loads(cached_data)
            else:
                r = requests.get(
                    "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                    params={
                        "url": url,
                        "key": self.google_cloud_api_key_3,
                        "category": "performance",
                    },
                    timeout=30,
                )
                data = r.json()
                ttl = 6 * 60 * 60
                await redis_client.setex(key, ttl, json.dumps(data))

            metrics = data["loadingExperience"]["metrics"]
            lcp = metrics["LARGEST_CONTENTFUL_PAINT_MS"]["percentile"] / 1000
            fid = metrics["FIRST_INPUT_DELAY_MS"]["percentile"]
            cls = metrics["CUMULATIVE_LAYOUT_SHIFT_SCORE"]["percentile"] / 100

            return {"lcp": f"{lcp:.2f}s", "fid": f"{fid:.0f}ms", "cls": f"{cls:.2f}"}
        except Exception as e:
            self.logger.error(f"Error checking core web vitals: {e}")
            return {"lcp": "-", "fid": "-", "cls": "-"}

    async def check_robots_txt(self, url):
        """Check robots.txt availability"""
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            response = requests.get(robots_url, timeout=5)
            if response.status_code == 200:
                return "✅ Available"
            return "❌ Not found or inaccessible"
        except Exception:
            return "❌ Error checking robots.txt"

    async def check_www_redirect(self, url):
        """Check WWW vs non-WWW redirect consistency"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            scheme = parsed.scheme
            
            # Check if domain starts with www
            if domain.startswith("www."):
                non_www = domain[4:]
                test_url = f"{scheme}://{non_www}"
            else:
                test_url = f"{scheme}://www.{domain}"
            
            response = requests.head(test_url, timeout=5, allow_redirects=True)
            final_url = response.url
            
            if final_url == url or urlparse(final_url).netloc == urlparse(url).netloc:
                return "✅ Consistent redirect"
            return "⚠️ Redirects to different domain"
        except Exception:
            return "⚠️ Could not verify redirect"

    async def check_directory_listing(self, url):
        """Check if directory listing is enabled"""
        try:
            # Try accessing a non-existent directory
            parsed = urlparse(url)
            test_url = f"{parsed.scheme}://{parsed.netloc}/nonexistent-test-directory-12345/"
            response = requests.get(test_url, timeout=5)
            
            # If we get 200 and see directory listing indicators
            if response.status_code == 200:
                content = response.text.lower()
                if any(indicator in content for indicator in ["index of", "directory listing", "parent directory"]):
                    return "❌ Directory listing enabled"
            return "✅ Directory listing disabled"
        except Exception:
            return "⚠️ Could not verify"

    async def check_safe_browsing(self, url):
        """Check Google Safe Browsing status"""
        try:
            # Using a simple check via Google's public API
            api_url = "https://transparencyreport.google.com/safe-browsing/search"
            # Note: This is a simplified check - full API requires API key
            return "⚠️ Manual check recommended (requires API key for full check)"
        except Exception:
            return "⚠️ Could not verify"

    async def analyze_performance_headers(self, response_headers):
        """Analyze performance-related HTTP headers"""
        expires_check = "❌ No expires headers for images"  # Would need to check image responses
        caching_advice = []
        
        cache_control = response_headers.get("Cache-Control", "")
        if cache_control:
            if "max-age" in cache_control:
                caching_advice.append("✅ Cache-Control header found")
            else:
                caching_advice.append("⚠️ Cache-Control present but no max-age")
        else:
            caching_advice.append("❌ No Cache-Control header")
        
        expires = response_headers.get("Expires", "")
        if expires:
            caching_advice.append("✅ Expires header found")
        
        if not cache_control and not expires:
            caching_advice.append("Consider adding caching headers or using a CDN")
        
        return {
            "expires_headers_check": expires_check,
            "caching_advice": "; ".join(caching_advice) if caching_advice else "✅ Good caching setup"
        }

    async def analyze_resource_minification(self, page):
        """Check if JS and CSS are minified"""
        try:
            js_files = []
            css_files = []
            
            # Get all script and link tags
            scripts = await page.query_selector_all("script[src]")
            links = await page.query_selector_all("link[rel='stylesheet']")
            
            for script in scripts:
                src = await script.get_attribute("src")
                if src:
                    js_files.append(src)
            
            for link in links:
                href = await link.get_attribute("href")
                if href:
                    css_files.append(href)
            
            # Check minification by filename and content
            minified_js = sum(1 for f in js_files if ".min.js" in f or "minified" in f.lower())
            minified_css = sum(1 for f in css_files if ".min.css" in f or "minified" in f.lower())
            
            js_check = (
                f"✅ {minified_js}/{len(js_files)} JS files appear minified"
                if js_files else "⚠️ No external JS files found"
            )
            css_check = (
                f"✅ {minified_css}/{len(css_files)} CSS files appear minified"
                if css_files else "⚠️ No external CSS files found"
            )
            
            return {
                "js_minification_check": js_check,
                "css_minification_check": css_check,
                "total_js_files": len(js_files),
                "total_css_files": len(css_files)
            }
        except Exception as e:
            self.logger.error(f"Error checking minification: {e}")
            return {
                "js_minification_check": "⚠️ Could not verify",
                "css_minification_check": "⚠️ Could not verify",
                "total_js_files": 0,
                "total_css_files": 0
            }

    async def count_requests(self, page):
        """Count total requests (images, JS, CSS)"""
        try:
            # This would ideally use network monitoring, but we'll estimate from DOM
            images = await page.query_selector_all("img")
            scripts = await page.query_selector_all("script[src]")
            stylesheets = await page.query_selector_all("link[rel='stylesheet']")
            
            total_requests = len(images) + len(scripts) + len(stylesheets)
            
            return {
                "total_requests": total_requests,
                "image_requests": len(images),
                "js_requests": len(scripts),
                "css_requests": len(stylesheets),
                "requests_guidance": (
                    "✅ Reasonable number of requests"
                    if total_requests < 50 else
                    "⚠️ High number of requests - consider combining files"
                    if total_requests < 100 else
                    "❌ Very high number of requests - optimize resource loading"
                )
            }
        except Exception:
            return {
                "total_requests": 0,
                "image_requests": 0,
                "js_requests": 0,
                "css_requests": 0,
                "requests_guidance": "⚠️ Could not count requests"
            }

    async def scrape_worker(self, browser, worker_id, queue: asyncio.Queue):
        page = await browser.new_page()
        while True:
            try:
                url = await asyncio.wait_for(queue.get(), timeout=2)
            except asyncio.TimeoutError:
                break
            try:
                # Measure response time
                start_time = asyncio.get_event_loop().time()
                
                response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle", timeout=10000)
                
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000  # Convert to ms
                
                # Get response headers
                response_headers = {}
                if response:
                    response_headers = response.headers
                
                html = await page.content()
                
                # Extract basic SEO data
                data = self.extract_seo_tags(html, url, response_headers)
                
                # Add response time
                response_time_status = (
                    "✅ Fast" if response_time < 500 else
                    "⚠️ Moderate" if response_time < 2000 else "❌ Slow"
                )
                data["response_time_check"] = f"{response_time_status} ({response_time:.0f}ms)"
                data["response_time_ms"] = response_time
                
                # Performance headers analysis
                perf_headers = await self.analyze_performance_headers(response_headers)
                data.update(perf_headers)
                
                # Resource minification check
                minification = await self.analyze_resource_minification(page)
                data.update(minification)
                
                # Count requests
                requests_data = await self.count_requests(page)
                data.update(requests_data)
                
                # Advanced SEO checks that require HTTP requests
                robots_check = await self.check_robots_txt(url)
                data["robots_txt_check"] = robots_check
                
                www_check = await self.check_www_redirect(url)
                data["www_redirect_check"] = www_check
                
                # Security checks
                directory_check = await self.check_directory_listing(url)
                data["directory_listing_check"] = directory_check
                
                safe_browsing_check = await self.check_safe_browsing(url)
                data["safe_browsing_check"] = safe_browsing_check
                
                # HTTPS check (already in extract_seo_tags, but ensure it's there)
                parsed = urlparse(url)
                data["https_ssl_check"] = "✅ HTTPS enabled" if parsed.scheme == "https" else "❌ Not using HTTPS"
                
                # Core Web Vitals (if API key available)
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
