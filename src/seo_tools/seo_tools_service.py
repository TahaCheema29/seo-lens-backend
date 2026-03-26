import time
from typing import Optional
from src.config.redis_client import redis_client
from src.config.logger_config import setup_logger
from src.seo_tools.utils.analyze_keyword_rank import KeywordRankChecker
from src.seo_tools.schemas.analyze_keyword_rank import AnalyzeKeywordRankRequest
from src.seo_tools.utils.suggest_keyword import KeywordResearch
from src.seo_tools.schemas.suggest_keywords import SuggestKeywordRequest
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoRequest, AnalyzeSiteSeoResponse
from src.seo_tools.utils.seo_crawler import SEOCrawler, URLStatus
from src.seo_tools.utils.seo_scraper import SEOScraper


class SeoToolsService:

    def __init__(self):
        self.logger = setup_logger(__name__)
            
    async def analyze_keyword_rank(self, user_input: AnalyzeKeywordRankRequest):
        
        checker = KeywordRankChecker(headless=True)
        print("Starting keyword rank checking...")
        results = await checker.run(
            keywords=user_input.keywords,
            target_domain=str(user_input.url),
            max_results=100
        )

        print(results)
        return results
    

    async def suggest_keywords(self, user_input: SuggestKeywordRequest):
        
        researcher = KeywordResearch(headless=True)
        print("Starting keyword rank checking...")
        results = await researcher.run(user_input.keywords)
        return results
    

    async def analyze_site_seo(self, user_input: AnalyzeSiteSeoRequest, crawl_id: Optional[str] = None) -> AnalyzeSiteSeoResponse:
      
        start_time = time.perf_counter()

        try:
            self.logger.info(f"Starting crawl for {user_input.url} with mode {user_input.crawl_mode}")
            crawler = SEOCrawler(
                start_url=user_input.url,
                crawl_mode=user_input.crawl_mode,
                crawl_id=crawl_id,
                redis_client=redis_client if crawl_id else None
            )
            crawled_data = await crawler.run()
            self.logger.info("Crawl completed, processing results...")

            if isinstance(crawled_data, dict):
                urls = [
                    url for url, status in crawled_data.items()
                    if status in [URLStatus.VISITED, URLStatus.SITEMAP, URLStatus.DISCOVERED]
                ]
            else:
                urls = crawled_data if isinstance(crawled_data, list) else list(crawled_data)

            self.logger.info(f"Crawled {len(urls)} URLs for scraping")
            print(f"Crawled {len(urls)} URLs for scraping")
            print("urls: ", urls[:5] if len(urls) > 5 else urls)
            
            if not urls:
                self.logger.warning("⚠️ No URLs to scrape")
                print("⚠️ No URLs to scrape")
                return []
            
            self.logger.info(f"Starting scraping for {len(urls)} URLs...")
            scraper = SEOScraper(user_input.url)
            results = await scraper.run(urls)
            self.logger.info("Scraping completed, saving results...")
            scraper.save_to_html()

            elapsed = time.perf_counter() - start_time
            self.logger.info(f"Done in {elapsed:.2f}s — {len(results.url_results)} pages analyzed")
            print(f"Done in {elapsed:.2f}s — {len(results.url_results)} pages analyzed")
            return results
            
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            error_msg = f"Error during SEO analysis after {elapsed:.2f}s: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            print(f"❌ {error_msg}")
            raise