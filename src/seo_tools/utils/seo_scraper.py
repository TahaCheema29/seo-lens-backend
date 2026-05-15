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
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoResult, BaseUrlChecks, AnalyzeSiteSeoResponse, CheckResult, CheckStatus

load_dotenv()
logger = setup_logger(__name__)


class SEOScraper:
    def __init__(self, start_url: str, max_workers: int = 15):
        self.start_url = start_url
        self.max_workers = max_workers
        self.results = []
        self.lock = asyncio.Lock()
        self.google_cloud_api_key_3 = settings.google_cloud_api_key_3
        self.logger = setup_logger(__name__)
        self.base_url_checks = None

    @staticmethod
    def extract_keywords_from_text(text):
        """Extract potential keywords from text"""
        if not text:
            return []
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
            guidance.append("Title is too short - aim for30-60 characters")
        elif length > 60:
            guidance.append("Title is too long - may be truncated in search results")
        
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

        h1_tags = [h.get_text(strip=True) for h in soup.find_all("h1")]
        h2_tags = [h.get_text(strip=True) for h in soup.find_all("h2")]
        h3_tags = [h.get_text(strip=True) for h in soup.find_all("h3")]

        if len(h1_tags) == 1:
            h1_check = CheckResult(
                status=CheckStatus.PASS,
                description="The page has exactly one H1 tag, which is optimal for SEO. Each page should have a single H1 tag that clearly describes the page content."
            )
        elif len(h1_tags) > 1:
            h1_check = CheckResult(
                status=CheckStatus.FAIL,
                description=f"Multiple H1 tags ({len(h1_tags)}) were found. Each page should have only one H1 tag for optimal SEO. Consider consolidating or removing extra H1 tags."
            )
        else:
            h1_check = CheckResult(
                status=CheckStatus.FAIL,
                description="No H1 tag was found on the page. H1 tags are important for SEO as they indicate the main heading of the page. Add an H1 tag with your primary keyword."
            )
        h1_keyword_guidance = "Consider including primary keyword in H1" if h1_tags else "Add an H1 tag with your primary keyword"
        
        h2_count = len(h2_tags)
        h2_guidance = (
            "✅ Good structure" if h2_count > 0 else "⚠️ Consider adding H2 tags for better content organization"
        )

        img_tags = soup.find_all("img")
        bad_alt_keywords = {"image", "photo", "picture", "img", "logo"}
        missing_or_poor_alts = [
            img
            for img in img_tags
            if not img.get("alt")
            or img.get("alt", "").strip().lower() in bad_alt_keywords
        ]
        if not missing_or_poor_alts:
            alt_check = CheckResult(
                status=CheckStatus.PASS,
                description="All images on the page have proper alt text, which improves accessibility and helps search engines understand image content."
            )
        else:
            alt_check = CheckResult(
                status=CheckStatus.FAIL,
                description=f"{len(missing_or_poor_alts)} out of {len(img_tags)} images are missing alt attributes or have generic alt text. Add descriptive alt text to all images for better SEO and accessibility."
            )

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

        canonical_tag = soup.find("link", rel="canonical")
        canonical = (
            canonical_tag["href"].strip()
            if canonical_tag and canonical_tag.get("href")
            else ""
        )
        if canonical:
            canonical_check = CheckResult(
                status=CheckStatus.PASS,
                description="The page has a canonical tag, which helps prevent duplicate content issues by specifying the preferred URL for the page."
            )
        else:
            canonical_check = CheckResult(
                status=CheckStatus.WARNING,
                description="No canonical tag was found. Adding a canonical tag helps prevent duplicate content issues and tells search engines which URL is the preferred version of the page."
            )

        noindex_meta = soup.find("meta", attrs={"name": "robots"})
        noindex_header = response_headers.get("X-Robots-Tag", "") if response_headers else ""
        has_noindex = (
            (noindex_meta and "noindex" in noindex_meta.get("content", "").lower()) or
            "noindex" in noindex_header.lower()
        )
        if has_noindex:
            noindex_check = CheckResult(
                status=CheckStatus.FAIL,
                description="The page has a noindex directive, which prevents search engines from indexing this page. Remove the noindex directive if you want this page to appear in search results."
            )
        else:
            noindex_check = CheckResult(
                status=CheckStatus.PASS,
                description="The page does not have a noindex directive, so it can be indexed by search engines."
            )

        og_tags = {
            "title": soup.find("meta", attrs={"property": "og:title"}),
            "type": soup.find("meta", attrs={"property": "og:type"}),
            "image": soup.find("meta", attrs={"property": "og:image"}),
            "url": soup.find("meta", attrs={"property": "og:url"}),
        }
        missing_og = [key for key, tag in og_tags.items() if not tag]
        if not missing_og:
            og_check = CheckResult(
                status=CheckStatus.PASS,
                description="All essential Open Graph tags (title, type, image, url) are present, which ensures proper display when the page is shared on social media platforms."
            )
        else:
            og_check = CheckResult(
                status=CheckStatus.WARNING,
                description=f"The page is missing some Open Graph tags ({', '.join(missing_og)}). Adding these tags improves how the page appears when shared on social media platforms like Facebook, Twitter, and LinkedIn."
            )

        schema_scripts = soup.find_all("script", type="application/ld+json")
        schema_types = []
        schema_validation = None
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
                    schema_validation = CheckResult(
                        status=CheckStatus.FAIL,
                        description="The page contains structured data, but the JSON-LD format is invalid. Fix the JSON-LD syntax to ensure search engines can properly parse the structured data."
                    )
            if not schema_validation:
                if schema_types:
                    schema_validation = CheckResult(
                        status=CheckStatus.PASS,
                        description=f"The page contains valid structured data (schema.org) with types: {', '.join(set(schema_types))}. This helps search engines better understand the page content."
                    )
                else:
                    schema_validation = CheckResult(
                        status=CheckStatus.WARNING,
                        description="The page contains structured data scripts, but no recognizable schema types were found. Ensure the JSON-LD contains valid @type properties."
                    )
        else:
            schema_validation = CheckResult(
                status=CheckStatus.WARNING,
                description="The page does not contain structured data (schema.org markup). Adding structured data helps search engines better understand your content and can improve visibility in search results with rich snippets."
            )

        html_size = len(html.encode('utf-8'))
        html_size_kb = html_size / 1024
        if html_size_kb < 100:
            html_size_check = CheckResult(
                status=CheckStatus.PASS,
                description=f"The HTML document size is {html_size_kb:.1f} KB, which is optimal for fast page loading."
            )
        elif html_size_kb < 500:
            html_size_check = CheckResult(
                status=CheckStatus.WARNING,
                description=f"The HTML document size is {html_size_kb:.1f} KB, which is larger than recommended. Consider optimizing the HTML by removing unnecessary code, minifying, or splitting content."
            )
        else:
            html_size_check = CheckResult(
                status=CheckStatus.FAIL,
                description=f"The HTML document size is {html_size_kb:.1f} KB, which is very large and will significantly impact page load times. Consider optimizing by removing unnecessary code, minifying HTML, or splitting content across multiple pages."
            )

        inline_styles = soup.find_all(style=True)
        inline_css_count = len(inline_styles)
        whitespace_ratio = len(re.findall(r'\s{3,}', html)) / max(len(html.split('\n')), 1)
        
        performance_warnings = []
        if inline_css_count > 10:
            performance_warnings.append(f"{inline_css_count} inline styles found - consider external CSS")
        if whitespace_ratio > 0.1:
            performance_warnings.append("Excessive whitespace detected - consider minification")
        
        performance_guidance = "; ".join(performance_warnings) if performance_warnings else "✅ No major issues detected"

        embedded_objects = soup.find_all(["object", "embed", "applet"])
        if not embedded_objects:
            embedded_check = CheckResult(
                status=CheckStatus.PASS,
                description="The page does not use deprecated embedded objects (object, embed, applet tags), which is good for modern web standards."
            )
        else:
            embedded_check = CheckResult(
                status=CheckStatus.WARNING,
                description=f"The page contains {len(embedded_objects)} deprecated embedded objects. Consider using HTML5 alternatives (like video, audio, or iframe tags) for better compatibility and performance."
            )

        viewport_tag = soup.find("meta", attrs={"name": "viewport"})
        if viewport_tag and "width=device-width" in viewport_tag.get("content", ""):
            mobile_responsiveness = CheckResult(
                status=CheckStatus.PASS,
                description="The page has a properly configured viewport meta tag, which ensures the page displays correctly on mobile devices."
            )
        else:
            mobile_responsiveness = CheckResult(
                status=CheckStatus.FAIL,
                description="The page is missing a viewport meta tag or it's not configured correctly. Add <meta name='viewport' content='width=device-width, initial-scale=1'> to ensure proper mobile display."
            )

        return {
            "url": url,
            "title": title,
            "title_length_check": CheckResult(
                status=CheckStatus.PASS if "✅" in title_quality['status'] else (CheckStatus.FAIL if "❌" in title_quality['status'] else CheckStatus.WARNING),
                description=title_quality['guidance']
            ),
            "title_keyword_presence": CheckResult(
                status=CheckStatus.PASS if title_keywords else CheckStatus.WARNING,
                description="Keywords found in title tag" if title_keywords else "Consider including relevant keywords in the title tag to improve SEO."
            ),
            "title_quality_guidance": title_quality['guidance'],
            "meta_description": meta_description,
            "meta_description_length_check": CheckResult(
                status=CheckStatus.PASS if "✅" in description_quality['status'] else (CheckStatus.FAIL if "❌" in description_quality['status'] else CheckStatus.WARNING),
                description=description_quality['guidance']
            ),
            "meta_description_keyword_presence": CheckResult(
                status=CheckStatus.PASS if desc_keywords else CheckStatus.WARNING,
                description="Keywords found in meta description" if desc_keywords else "Consider including relevant keywords in the meta description to improve SEO."
            ),
            "meta_description_quality_guidance": description_quality['guidance'],
            "meta_keywords": meta_keywords,
            "h1_check": h1_check,
            "h1_keyword_guidance": h1_keyword_guidance,
            "h1": h1_tags[0] if h1_tags else "",
            "h2_count": h2_count,
            "h2_optimization_guidance": h2_guidance,
            "h2": " | ".join(h2_tags[:5]),
            "h3": " | ".join(h3_tags[:5]),
            "image_alt_check": alt_check,
            "internal_links_count": internal_count,
            "external_links_count": external_count,
            "links_quality_guidance": links_guidance_text,
            "canonical_check": canonical_check, 
            "canonical": canonical,  
            "noindex_check": noindex_check,   
            "open_graph_check": og_check,   
            "schema_validation": schema_validation,     
            "html_size_check": html_size_check,
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
                return CheckResult(
                    status=CheckStatus.PASS,
                    description="The robots.txt file is accessible and can be used by search engines to understand crawling rules."
                )
            return CheckResult(
                status=CheckStatus.FAIL,
                description="The robots.txt file is missing or cannot be accessed. This may prevent proper search engine crawling control."
            )
        except Exception as e:
            return CheckResult(
                status=CheckStatus.FAIL,
                description=f"Could not verify robots.txt availability: {str(e)}"
            )

    async def check_www_redirect(self, url):
        """Check WWW vs non-WWW redirect consistency"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            scheme = parsed.scheme
            
            if domain.startswith("www."):
                non_www = domain[4:]
                test_url = f"{scheme}://{non_www}"
            else:
                test_url = f"{scheme}://www.{domain}"
            
            response = requests.head(test_url, timeout=5, allow_redirects=True)
            final_url = response.url
            
            if final_url == url or urlparse(final_url).netloc == urlparse(url).netloc:
                return CheckResult(
                    status=CheckStatus.PASS,
                    description="The site properly redirects between www and non-www versions, ensuring consistent URL structure."
                )
            return CheckResult(
                status=CheckStatus.WARNING,
                description="The redirect between www and non-www versions may not be properly configured, which could cause duplicate content issues."
            )
        except Exception as e:
            return CheckResult(
                status=CheckStatus.WARNING,
                description=f"Unable to check redirect consistency: {str(e)}"
            )

    async def check_directory_listing(self, url):
        """Check if directory listing is enabled"""
        try:
            parsed = urlparse(url)
            test_url = f"{parsed.scheme}://{parsed.netloc}/nonexistent-test-directory-12345/"
            response = requests.get(test_url, timeout=5)
            
            if response.status_code == 200:
                content = response.text.lower()
                if any(indicator in content for indicator in ["index of", "directory listing", "parent directory"]):
                    return CheckResult(
                        status=CheckStatus.FAIL,
                        description="Directory listing is enabled, which can expose sensitive files and directory structure to unauthorized users."
                    )
            return CheckResult(
                status=CheckStatus.PASS,
                description="Directory listing is properly disabled, preventing unauthorized access to directory contents."
            )
        except Exception as e:
            return CheckResult(
                status=CheckStatus.WARNING,
                description=f"Unable to check directory listing status: {str(e)}"
            )


    async def check_base_url(self, base_url: str) -> BaseUrlChecks:
        """Perform checks that should only be done on the base URL"""
        base_url_str = str(base_url) if base_url else ""
        parsed = urlparse(base_url_str)
        base_domain = f"{parsed.scheme}://{parsed.netloc}"
        
        www_check = await self.check_www_redirect(base_domain)
        robots_check = await self.check_robots_txt(base_domain)
        
        if parsed.scheme == "https":
            https_check = CheckResult(
                status=CheckStatus.PASS,
                description="The site uses HTTPS encryption, which is essential for security and SEO. Search engines prefer HTTPS sites."
            )
        else:
            https_check = CheckResult(
                status=CheckStatus.FAIL,
                description="The site is not using HTTPS encryption. This is a security risk and can negatively impact SEO rankings. Consider implementing SSL/TLS certificates."
            )
        
        directory_check = await self.check_directory_listing(base_domain)
        
        try:
            response = requests.get(base_domain, timeout=10, allow_redirects=True)
            response_headers = response.headers
            perf_headers = await self.analyze_performance_headers(response_headers)
            expires_check = perf_headers.get("expires_headers_check")
            caching_advice = perf_headers.get("caching_advice")
        except Exception as e:
            self.logger.error(f"Error checking performance headers for base URL: {e}")
            expires_check = CheckResult(
                status=CheckStatus.WARNING,
                description=f"Error checking performance headers: {str(e)}"
            )
            caching_advice = CheckResult(
                status=CheckStatus.WARNING,
                description=f"Error checking caching headers: {str(e)}"
            )
        
        return BaseUrlChecks(
            base_url=base_domain,
            www_redirect_check=www_check,
            robots_txt_check=robots_check,
            https_ssl_check=https_check,
            directory_listing_check=directory_check,
            expires_headers_check=expires_check,
            caching_advice=caching_advice,
        )

    async def analyze_performance_headers(self, response_headers):
        """Analyze performance-related HTTP headers"""
        expires_check = CheckResult(
            status=CheckStatus.WARNING,
            description="To fully verify expires headers, individual image responses need to be checked. This is a simplified check."
        )
        
        cache_control = response_headers.get("Cache-Control", "")
        expires = response_headers.get("Expires", "")
        
        if cache_control and "max-age" in cache_control:
            caching_advice = CheckResult(
                status=CheckStatus.PASS,
                description="The site has proper caching headers configured, which helps improve page load times for returning visitors."
            )
        elif cache_control:
            caching_advice = CheckResult(
                status=CheckStatus.WARNING,
                description="Cache-Control header exists but doesn't specify max-age. Consider adding max-age for better caching control."
            )
        elif expires:
            caching_advice = CheckResult(
                status=CheckStatus.PASS,
                description="The site uses Expires headers for caching, which helps improve performance."
            )
        else:
            caching_advice = CheckResult(
                status=CheckStatus.FAIL,
                description="No Cache-Control or Expires headers detected. Consider adding caching headers or using a CDN to improve page load times."
            )
        
        return {
            "expires_headers_check": expires_check,
            "caching_advice": caching_advice
        }

    async def analyze_resource_minification(self, page):
        """Check if JS and CSS are minified"""
        try:
            js_files = []
            css_files = []
            
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
            
            minified_js = sum(1 for f in js_files if ".min.js" in f or "minified" in f.lower())
            minified_css = sum(1 for f in css_files if ".min.css" in f or "minified" in f.lower())
            
            if js_files:
                if minified_js == len(js_files):
                    js_check = CheckResult(
                        status=CheckStatus.PASS,
                        description=f"All {len(js_files)} JavaScript files appear to be minified, which reduces file size and improves page load times."
                    )
                elif minified_js > 0:
                    js_check = CheckResult(
                        status=CheckStatus.WARNING,
                        description=f"Only {minified_js} out of {len(js_files)} JavaScript files appear to be minified. Consider minifying all JS files to improve performance."
                    )
                else:
                    js_check = CheckResult(
                        status=CheckStatus.WARNING,
                        description=f"None of the {len(js_files)} JavaScript files appear to be minified. Minifying JS files can significantly reduce file size and improve page load times."
                    )
            else:
                js_check = CheckResult(
                    status=CheckStatus.WARNING,
                    description="No external JavaScript files were detected on the page."
                )
            
            if css_files:
                if minified_css == len(css_files):
                    css_check = CheckResult(
                        status=CheckStatus.PASS,
                        description=f"All {len(css_files)} CSS files appear to be minified, which reduces file size and improves page load times."
                    )
                elif minified_css > 0:
                    css_check = CheckResult(
                        status=CheckStatus.WARNING,
                        description=f"Only {minified_css} out of {len(css_files)} CSS files appear to be minified. Consider minifying all CSS files to improve performance."
                    )
                else:
                    css_check = CheckResult(
                        status=CheckStatus.WARNING,
                        description=f"None of the {len(css_files)} CSS files appear to be minified. Minifying CSS files can significantly reduce file size and improve page load times."
                    )
            else:
                css_check = CheckResult(
                    status=CheckStatus.WARNING,
                    description="No external CSS files were detected on the page."
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
                "js_minification_check": CheckResult(
                    status=CheckStatus.WARNING,
                    description=f"Error checking JavaScript minification: {str(e)}"
                ),
                "css_minification_check": CheckResult(
                    status=CheckStatus.WARNING,
                    description=f"Error checking CSS minification: {str(e)}"
                ),
                "total_js_files": 0,
                "total_css_files": 0
            }

    async def count_requests(self, page):
        """Count total requests (images, JS, CSS)"""
        try:
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

    async def scrape_worker(self, browser, worker_id, queue: asyncio.Queue, core_web_vitals_task=None):
        page = await browser.new_page()
        while True:
            try:
                url = await asyncio.wait_for(queue.get(), timeout=2)
            except asyncio.TimeoutError:
                break
            try:
                start_time = asyncio.get_event_loop().time()
                
                response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle", timeout=10000)
                
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                response_headers = {}
                if response:
                    response_headers = response.headers
                
                html = await page.content()
                
                data = self.extract_seo_tags(html, url, response_headers)
                
                if response_time < 500:
                    data["response_time_check"] = CheckResult(
                        status=CheckStatus.PASS,
                        description=f"The page loads quickly with a response time of {response_time:.0f}ms, which is excellent for user experience and SEO."
                    )
                elif response_time < 2000:
                    data["response_time_check"] = CheckResult(
                        status=CheckStatus.WARNING,
                        description=f"The page response time is {response_time:.0f}ms, which is acceptable but could be improved. Consider optimizing server response time, reducing server-side processing, or using a CDN."
                    )
                else:
                    data["response_time_check"] = CheckResult(
                        status=CheckStatus.FAIL,
                        description=f"The page response time is {response_time:.0f}ms, which is slow and can negatively impact user experience and SEO rankings. Consider optimizing server performance, reducing server-side processing, using caching, or implementing a CDN."
                    )
                data["response_time_ms"] = response_time
                
                minification = await self.analyze_resource_minification(page)
                data.update(minification)
                
                requests_data = await self.count_requests(page)
                data.update(requests_data)
                
                # Only check Core Web Vitals for base URL (homepage) to improve performance
                # Internal pages get placeholder values as they typically have similar performance
                parsed_url = urlparse(url)
                base_parsed = urlparse(str(self.start_url))
                is_base_url = (parsed_url.netloc == base_parsed.netloc and 
                               parsed_url.path.rstrip('/') == base_parsed.path.rstrip('/'))
                
                if self.google_cloud_api_key_3 and is_base_url and core_web_vitals_task:
                    print(f"📊 Awaiting Core Web Vitals for base URL: {url}")
                    try:
                        # Wait for the parallel API call to complete (or timeout)
                        vitals = await asyncio.wait_for(core_web_vitals_task, timeout=35.0)
                        print(f"✅ Core Web Vitals received: {vitals}")
                        data.update(vitals)
                    except asyncio.TimeoutError:
                        print(f"⚠️ Core Web Vitals API timeout for {url}")
                        data.update({"lcp": "-", "fid": "-", "cls": "-"})
                    except Exception as e:
                        print(f"⚠️ Core Web Vitals API error for {url}: {e}")
                        data.update({"lcp": "-", "fid": "-", "cls": "-"})
                else:
                    # Skip Core Web Vitals for internal pages - use placeholder values
                    # This significantly improves performance while maintaining data structure
                    data.update({"lcp": "-", "fid": "-", "cls": "-"})

                async with self.lock:
                    self.results.append(data)

                print("result is ", self.results)

            except Exception as e:
                self.logger.error(f"Worker {worker_id} failed on {url}: {e}")
            finally:
                queue.task_done()

        await page.close()
        print(f"✅ Worker {worker_id} finished")

    async def run(self, urls):
        """Run scraping process for all URLs with parallel Core Web Vitals fetching"""
        self.base_url_checks = await self.check_base_url(self.start_url)
        
        # Start Core Web Vitals API call in parallel (non-blocking)
        # This fetches performance metrics while scraping happens concurrently
        core_web_vitals_task = None
        base_url_str = str(self.start_url).rstrip('/')
        
        if self.google_cloud_api_key_3:
            print(f"🚀 Starting parallel Core Web Vitals fetch for base URL: {base_url_str}")
            core_web_vitals_task = asyncio.create_task(
                self.check_core_web_vitals(base_url_str)
            )
        
        queue = asyncio.Queue()
        for url in urls:
            await queue.put(url)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            tasks = [
                self.scrape_worker(browser, i, queue, core_web_vitals_task) 
                for i in range(self.max_workers)
            ]
            await asyncio.gather(*tasks)
            await browser.close()

        validated_results = [AnalyzeSiteSeoResult(**res) for res in self.results]
        
        return AnalyzeSiteSeoResponse(
            base_url_checks=self.base_url_checks,
            url_results=validated_results
        )

    def save_to_html(self, filename="seo_results.html"):
        """Save scraped SEO results to a styled HTML file"""
        if not self.results:
            print("⚠️ No results to save")
            return

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
                h2 {
                    color: #1e3a8a;
                    margin-top: 30px;
                    margin-bottom: 15px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    border-radius: 8px;
                    overflow: hidden;
                    margin-bottom: 30px;
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

        html = [
            "<html><head><meta charset='UTF-8'><title>SEO Results</title>",
            style,
            "</head><body>",
        ]
        html.append("<h1>Verdant Soft – SEO Audit Results</h1>")
        
        if self.base_url_checks:
            html.append("<h2>Base URL Checks</h2>")
            html.append("<table><thead><tr><th>Check</th><th>Status</th><th>Description</th></tr></thead><tbody>")
            base_checks_dict = self.base_url_checks.model_dump()
            for key, value in base_checks_dict.items():
                if key != "base_url" and value:
                    check_name = key.replace("_", " ").title()
                    if isinstance(value, dict) and "status" in value:
                        status = value.get("status", "UNKNOWN")
                        description = value.get("description", "N/A")
                        
                        if status == "PASS":
                            status_class = "status-ok"
                            status_icon = "✅"
                        elif status == "FAIL":
                            status_class = "status-bad"
                            status_icon = "❌"
                        else:
                            status_class = "status-warning"
                            status_icon = "⚠️"
                        
                        cell_class = f" class='{status_class}'" if status_class else ""
                        html.append(f"<tr><td>{check_name}</td><td{cell_class}>{status_icon} {status}</td><td>{description}</td></tr>")
                    else:
                        html.append(f"<tr><td>{check_name}</td><td>N/A</td><td>{str(value)}</td></tr>")
            html.append("</tbody></table>")
        
        if self.results:
            html.append("<h2>Per-URL Results</h2>")
            html.append("<table><thead><tr>")
            
            for header in self.results[0].keys():
                html.append(f"<th>{header}</th>")
            html.append("</tr></thead><tbody>")

            for row in self.results:
                html.append("<tr>")
                for key, value in row.items():
                    if key.lower() == "url":
                        cell = f"<a href='{value}' target='_blank'>{value}</a>"
                    elif "✅" in str(value):
                        cell = f"<span class='status-ok'>{value}</span>"
                    elif "❌" in str(value):
                        cell = f"<span class='status-bad'>{value}</span>"
                    else:
                        cell = value or ""
                    html.append(f"<td>{cell}</td>")
                html.append("</tr>")
            html.append("</tbody></table>")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html.append(f"<footer>Generated on {timestamp}</footer>")
        html.append("</body></html>")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("".join(html))

        print(f"📄 SEO results saved to {filename}")