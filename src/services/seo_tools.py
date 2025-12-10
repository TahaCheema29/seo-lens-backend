import time
from src.utils.analyze_keyword_rank import KeywordRankChecker
from src.schemas.analyze_keyword_rank import AnalyzeKeywordRankRequest
from src.utils.suggest_keyword import KeywordResearch
from src.schemas.suggest_keywords import SuggestKeywordRequest
from src.schemas.analyze_site_seo import AnalyzeSiteSeoRequest, AnalyzeSiteSeoResponse
from src.utils.seo_crawler import SEOCrawler
from src.utils.seo_scraper import SEOScraper


class SeoToolsService:

    async def analyze_keyword_rank(self,user_input:AnalyzeKeywordRankRequest):
        
        checker = KeywordRankChecker(headless=True)
        print("Starting keyword rank checking...")
        results = await checker.run(
            keywords=user_input.keywords,
            target_domain=str(user_input.url),
            max_results=100
        )

        print(results)
        return results
    

    async def suggest_keywords(self,user_input:SuggestKeywordRequest):
        
        researcher = KeywordResearch(headless=True)
        print("Starting keyword rank checking...")
        results = await researcher.run(user_input.keywords)
        return results
    

    async def analyze_site_seo(self,user_input:AnalyzeSiteSeoRequest)-> AnalyzeSiteSeoResponse:
      
        start_time = time.perf_counter()

        # 1. Crawl URLs
        crawler = SEOCrawler(user_input.url, crawl_mode=user_input.crawl_mode)
        urls = await crawler.run()

        print("url is ",urls)
        # 2. Scrape SEO Data
        scraper = SEOScraper(str(user_input.url))
        results = await scraper.run(urls)
        scraper.save_to_html()

        print(f"Done in {time.perf_counter() - start_time:.2f}s — {len(results.url_results)} pages analyzed")
        return results