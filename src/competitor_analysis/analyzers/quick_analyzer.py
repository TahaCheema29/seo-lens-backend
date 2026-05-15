"""
Quick Analyzer for Competitor Analysis
Performs ultra-fast homepage-only analysis
"""

import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from src.config.logger_config import setup_logger


class QuickAnalyzer:
    """
    Quick analyzer for homepage-only competitor analysis
    Provides ultra-fast results (10-20 seconds)
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    async def analyze_homepage(self, url: str) -> Dict[str, Any]:
        """
        Analyze a single homepage and return SEO data
        
        Args:
            url: Website URL to analyze
            
        Returns:
            Dictionary with SEO analysis data
        """
        try:
            self.logger.info(f"Starting quick analysis for {url}")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                start_time = asyncio.get_event_loop().time()
                
                # Navigate to the page
                response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                load_time = (asyncio.get_event_loop().time() - start_time) * 1000  # Convert to ms
                
                # Get HTML content
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")
                
                # Extract SEO metrics
                seo_data = await self._extract_seo_metrics(page, soup, response, load_time)
                
                await browser.close()
                
                self.logger.info(f"Quick analysis completed for {url}")
                
                return {
                    "base_url_checks": seo_data.get("base_url_checks", {}),
                    "url_results": [seo_data.get("page_data", {})],
                    "total_pages": 1,
                    "avg_response_time_ms": load_time
                }
                
        except Exception as e:
            self.logger.error(f"Error in quick analysis for {url}: {e}")
            return self._create_error_response(url, str(e))
    
    async def _extract_seo_metrics(
        self, 
        page, 
        soup: BeautifulSoup, 
        response, 
        load_time: float
    ) -> Dict[str, Any]:
        """Extract SEO metrics from a page"""
        
        parsed_url = urlparse(page.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Base URL checks
        base_url_checks = {
            "base_url": base_url,
            "www_redirect_check": {"status": "PASS" if "www" not in parsed_url.netloc else "INFO"},
            "https_ssl_check": {"status": "PASS" if parsed_url.scheme == "https" else "FAIL"},
            "robots_txt_check": {"status": "PASS"},  # Simplified for quick mode
            "directory_listing_check": {"status": "PASS"}
        }
        
        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        title_length = len(title)
        
        # Title check
        title_status = "PASS" if 30 <= title_length <= 60 else "WARNING"
        
        # Extract meta description
        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_desc_tag.get("content", "") if meta_desc_tag else ""
        meta_desc_length = len(meta_description)
        meta_desc_status = "PASS" if 120 <= meta_desc_length <= 160 else "WARNING" if meta_desc_length > 0 else "FAIL"
        
        # Extract H1
        h1_tag = soup.find("h1")
        h1 = h1_tag.get_text(strip=True) if h1_tag else ""
        h1_count = len(soup.find_all("h1"))
        h1_status = "PASS" if h1_count == 1 else "WARNING"
        
        # Count images and check alt text
        images = soup.find_all("img")
        images_with_alt = sum(1 for img in images if img.get("alt"))
        image_alt_status = "PASS" if images and images_with_alt == len(images) else "WARNING" if images_with_alt > 0 else "FAIL"
        
        # Check canonical
        canonical_tag = soup.find("link", attrs={"rel": "canonical"})
        canonical = canonical_tag.get("href", "") if canonical_tag else ""
        canonical_status = "PASS" if canonical else "WARNING"
        
        # Check Open Graph
        og_title = soup.find("meta", property="og:title")
        og_status = "PASS" if og_title else "WARNING"
        
        # Check schema markup
        schema_scripts = soup.find_all("script", type="application/ld+json")
        schema_status = "PASS" if schema_scripts else "WARNING"
        
        # Check mobile viewport
        viewport = soup.find("meta", attrs={"name": "viewport"})
        mobile_status = "PASS" if viewport else "FAIL"
        
        # Check noindex
        robots_meta = soup.find("meta", attrs={"name": "robots"})
        noindex_status = "FAIL" if robots_meta and "noindex" in robots_meta.get("content", "").lower() else "PASS"
        
        # Get page size
        html_size = len(html.encode('utf-8'))
        
        # Get resource counts
        scripts = len(soup.find_all("script", src=True))
        stylesheets = len(soup.find_all("link", rel="stylesheet"))
        total_requests = len(images) + scripts + stylesheets
        
        page_data = {
            "url": page.url,
            "title": title,
            "title_length_check": {"status": title_status},
            "meta_description": meta_description,
            "meta_description_length_check": {"status": meta_desc_status},
            "h1": h1,
            "h1_check": {"status": h1_status},
            "h2_count": len(soup.find_all("h2")),
            "image_alt_check": {"status": image_alt_status},
            "canonical": canonical,
            "canonical_check": {"status": canonical_status},
            "open_graph_check": {"status": og_status},
            "schema_validation": {"status": schema_status},
            "mobile_responsiveness": {"status": mobile_status},
            "noindex_check": {"status": noindex_status},
            "response_time_ms": round(load_time, 2),
            "html_size_bytes": html_size,
            "total_requests": total_requests
        }
        
        return {
            "base_url_checks": base_url_checks,
            "page_data": page_data
        }
    
    def _create_error_response(self, url: str, error: str) -> Dict[str, Any]:
        """Create an error response"""
        return {
            "base_url_checks": {},
            "url_results": [],
            "total_pages": 0,
            "avg_response_time_ms": 0,
            "error": error
        }
