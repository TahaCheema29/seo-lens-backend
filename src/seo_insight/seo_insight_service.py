from typing import List, Optional
from statistics import mean
from src.seo_insight.repository.seo_insight_repository import SeoInsightRepository
from src.models.seo_insight import SeoInsightResult
from src.seo_tools.utils.seo_crawler import SEOCrawler, URLStatus, CrawlMode
from src.seo_tools.utils.seo_scraper import SEOScraper
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoResponse
from src.config.redis_client import redis_client
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class SeoInsightService:
    """Service for SEO insight operations"""
    
    def __init__(self, repo: SeoInsightRepository):
        self.repo = repo
    
    async def analyze(
        self,
        target_url: str,
        crawl_mode: str,
        crawl_id: Optional[str] = None
    ) -> AnalyzeSiteSeoResponse:
        """Analyze site SEO"""
        mode = CrawlMode.FULL_CRAWL if crawl_mode == "FULL_CRAWL" else CrawlMode.SITEMAP_ONLY
        
        crawler = SEOCrawler(
            start_url=target_url,
            crawl_mode=mode,
            crawl_id=crawl_id,
            redis_client=redis_client if crawl_id else None
        )
        
        crawled_data = await crawler.run()
        
        if isinstance(crawled_data, dict):
            urls = [
                url for url, status in crawled_data.items()
                if status in [URLStatus.VISITED, URLStatus.SITEMAP, URLStatus.DISCOVERED]
            ]
        else:
            urls = crawled_data if isinstance(crawled_data, list) else list(crawled_data)
        
        if not urls:
            return AnalyzeSiteSeoResponse(base_url_checks={}, url_results=[])
        
        scraper = SEOScraper(target_url)
        results = await scraper.run(urls)
        
        return results
    
    async def analyze_and_save(
        self,
        user_id: str,
        target_url: str,
        crawl_mode: str,
        crawl_id: Optional[str] = None,
        save_result: bool = True
    ) -> dict:
        """Analyze site SEO and save results"""
        try:
            result = await self.analyze(target_url, crawl_mode, crawl_id)
            
            if save_result and result:
                base_url_checks_dict = result.base_url_checks.model_dump() if result.base_url_checks else {}
                url_results_list = [r.model_dump() for r in result.url_results] if result.url_results else []
                
                avg_response_time = None
                response_times = [r.get("response_time_ms") for r in url_results_list if r.get("response_time_ms")]
                if response_times:
                    avg_response_time = mean(response_times)
                
                db_result = SeoInsightResult(
                    user_id=user_id,
                    target_url=target_url,
                    crawl_mode=crawl_mode,
                    base_url_checks=base_url_checks_dict,
                    url_results=url_results_list,
                    total_pages=len(url_results_list),
                    avg_response_time_ms=avg_response_time,
                )
                await self.repo.create(db_result)
            
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="SEO analysis completed successfully",
                data=result
            )
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to analyze site SEO: {str(e)}",
                data=None
            )
    
    async def get_by_user(self, user_id: str, skip: int, limit: int) -> dict:
        """Get results for a user"""
        try:
            items = await self.repo.get_by_user(user_id, skip, limit)
            total = await self.repo.count_by_user(user_id)
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Results retrieved successfully",
                data={"items": items, "total": total}
            )
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to retrieve results: {str(e)}",
                data=None
            )
    
    async def get_by_id(self, user_id: str, result_id: str) -> dict:
        """Get a specific result"""
        try:
            result = await self.repo.get_by_user_and_id(user_id, result_id)
            if not result:
                return create_response(
                    status=RESPONSE_STATUS_ERROR,
                    message="Result not found",
                    data=None
                )
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Result retrieved successfully",
                data=result
            )
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to retrieve result: {str(e)}",
                data=None
            )
    
    async def delete(self, user_id: str, result_id: str) -> dict:
        """Delete a result"""
        try:
            result = await self.repo.get_by_user_and_id(user_id, result_id)
            if not result:
                return create_response(
                    status=RESPONSE_STATUS_ERROR,
                    message="Result not found",
                    data=None
                )
            deleted = await self.repo.delete(result_id)
            if not deleted:
                return create_response(
                    status=RESPONSE_STATUS_ERROR,
                    message="Failed to delete result",
                    data=None
                )
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Result deleted successfully",
                data=None
            )
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to delete result: {str(e)}",
                data=None
            )