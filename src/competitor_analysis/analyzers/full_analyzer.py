"""
Full Analyzer for Competitor Analysis
Performs comprehensive analysis with 100 page limit
Uses existing SEOCrawler and SEOScraper
"""

from typing import Dict, Any
from src.seo_tools.utils.seo_crawler import SEOCrawler, CrawlMode, URLStatus
from src.seo_tools.utils.seo_scraper import SEOScraper
from src.config.logger_config import setup_logger


class FullAnalyzer:
    """
    Full analyzer for comprehensive competitor analysis
    Analyzes up to 100 pages per site
    Supports both SITEMAP_ONLY and FULL_CRAWL modes
    """
    
    MAX_PAGES = 100  # Maximum pages to analyze per site
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    async def analyze_site(
        self, 
        url: str, 
        crawl_mode: CrawlMode
    ) -> Dict[str, Any]:
        """
        Analyze a website comprehensively
        
        Args:
            url: Website URL to analyze
            crawl_mode: SITEMAP_ONLY or FULL_CRAWL
            
        Returns:
            Dictionary with comprehensive SEO analysis data
        """
        try:
            self.logger.info(f"Starting full analysis for {url} with mode {crawl_mode.value}")
            
            # Step 1: Crawl the site
            crawler = SEOCrawler(
                start_url=url,
                crawl_mode=crawl_mode,
                max_workers=5
            )
            
            crawled_data = await crawler.run()
            
            # Process crawled data
            if isinstance(crawled_data, dict):
                urls = [
                    url for url, status in crawled_data.items()
                    if status in [URLStatus.VISITED, URLStatus.SITEMAP, URLStatus.DISCOVERED]
                ]
            else:
                urls = crawled_data if isinstance(crawled_data, list) else list(crawled_data)
            
            # Limit to MAX_PAGES
            if len(urls) > self.MAX_PAGES:
                self.logger.info(f"Limiting analysis from {len(urls)} to {self.MAX_PAGES} pages")
                urls = urls[:self.MAX_PAGES]
            
            if not urls:
                self.logger.warning(f"No URLs found for {url}")
                return self._create_empty_response(url)
            
            self.logger.info(f"Crawled {len(urls)} URLs for {url}")
            
            # Step 2: Scrape the pages
            scraper = SEOScraper(url)
            results = await scraper.run(urls)
            
            self.logger.info(f"Scraping completed for {url}")
            
            # Convert results to dictionary format
            return self._convert_to_dict(results, len(urls))
            
        except Exception as e:
            self.logger.error(f"Error in full analysis for {url}: {e}")
            return self._create_error_response(url, str(e))
    
    def _convert_to_dict(self, results, total_pages: int) -> Dict[str, Any]:
        """Convert scraper results to dictionary format"""
        
        if hasattr(results, 'model_dump'):
            # It's a Pydantic model
            data = results.model_dump()
        elif isinstance(results, dict):
            data = results
        else:
            # Try to convert to dict
            data = dict(results)
        
        # Extract base_url_checks
        base_url_checks = data.get("base_url_checks", {})
        if hasattr(base_url_checks, 'model_dump'):
            base_url_checks = base_url_checks.model_dump()
        
        # Extract url_results
        url_results = data.get("url_results", [])
        results_list = []
        
        for result in url_results:
            if hasattr(result, 'model_dump'):
                results_list.append(result.model_dump())
            elif isinstance(result, dict):
                results_list.append(result)
        
        # Calculate average response time
        response_times = [
            r.get("response_time_ms", 0) 
            for r in results_list 
            if r.get("response_time_ms")
        ]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "base_url_checks": base_url_checks,
            "url_results": results_list,
            "total_pages": total_pages,
            "avg_response_time_ms": round(avg_response, 2)
        }
    
    def _create_empty_response(self, url: str) -> Dict[str, Any]:
        """Create an empty response when no URLs are found"""
        return {
            "base_url_checks": {
                "base_url": url,
                "www_redirect_check": {"status": "UNKNOWN"},
                "https_ssl_check": {"status": "UNKNOWN"},
                "robots_txt_check": {"status": "UNKNOWN"},
                "directory_listing_check": {"status": "UNKNOWN"}
            },
            "url_results": [],
            "total_pages": 0,
            "avg_response_time_ms": 0
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
