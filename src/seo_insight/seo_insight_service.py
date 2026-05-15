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
                
                # Calculate simple pass/fail score
                score = self._calculate_score(base_url_checks_dict, url_results_list)
                
                db_result = SeoInsightResult(
                    user_id=user_id,
                    target_url=target_url,
                    crawl_mode=crawl_mode,
                    base_url_checks=base_url_checks_dict,
                    url_results=url_results_list,
                    total_pages=len(url_results_list),
                    avg_response_time_ms=avg_response_time,
                    score=score
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
            await self.repo.delete(result)
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
    
    async def get_stats(self, user_id: str) -> dict:
        """Get statistics for user's SEO insights"""
        from src.models.seo_insight import AnalysisStatus
        from sqlalchemy import func, select
        
        try:
            items = await self.repo.get_by_user(user_id, skip=0, limit=1000)
            
            total_critical = 0
            total_warnings = 0
            total_passed = 0
            scores = []
            
            completed_count = 0
            processing_count = 0
            failed_count = 0
            pending_count = 0
            
            for item in items:
                status_value = item.status.value if hasattr(item.status, 'value') else str(item.status)
                
                if status_value == AnalysisStatus.COMPLETED.value:
                    completed_count += 1
                elif status_value == AnalysisStatus.PROCESSING.value:
                    processing_count += 1
                elif status_value == AnalysisStatus.FAILED.value:
                    failed_count += 1
                elif status_value == AnalysisStatus.PENDING.value:
                    pending_count += 1
                
                # Use stored score if available
                if hasattr(item, 'score') and item.score is not None:
                    scores.append(item.score)
                elif item.base_url_checks:
                    # Calculate simple score from checks
                    score = self._calculate_score(item.base_url_checks, item.url_results if hasattr(item, 'url_results') else [])
                    scores.append(score)
            
            avg_score = mean(scores) if scores else 0.0
            
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Stats retrieved successfully",
                data={
                    "avg_score": round(avg_score, 2),
                    "total_critical": total_critical,
                    "total_warnings": total_warnings,
                    "total_passed": total_passed,
                    "completed_count": completed_count,
                    "processing_count": processing_count,
                    "failed_count": failed_count,
                    "pending_count": pending_count
                }
            )
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to get stats: {str(e)}",
                data=None
            )
    
    def _calculate_score(self, base_url_checks: dict, url_results: list) -> int:
        """Calculate simple pass/fail score: PASS=100%, WARNING=50%, FAIL=0%"""
        total_checks = 0
        passed_checks = 0
        warning_checks = 0
        failed_checks = 0
        
        # Count base URL checks
        base_checks = [
            base_url_checks.get('www_redirect_check'),
            base_url_checks.get('robots_txt_check'),
            base_url_checks.get('https_ssl_check'),
            base_url_checks.get('directory_listing_check'),
            base_url_checks.get('expires_headers_check'),
            base_url_checks.get('caching_advice'),
        ]
        
        for check in base_checks:
            if check:
                status = check.get('status', '')
                total_checks += 1
                if status == 'PASS':
                    passed_checks += 1
                elif status == 'WARNING':
                    warning_checks += 1
                elif status == 'FAIL':
                    failed_checks += 1
        
        # Count URL result checks
        for result in url_results:
            if not isinstance(result, dict):
                continue
            checks = [
                result.get('title_length_check'),
                result.get('title_keyword_presence'),
                result.get('meta_description_length_check'),
                result.get('meta_description_keyword_presence'),
                result.get('h1_check'),
                result.get('image_alt_check'),
                result.get('canonical_check'),
                result.get('noindex_check'),
                result.get('open_graph_check'),
                result.get('schema_validation'),
                result.get('html_size_check'),
                result.get('response_time_check'),
                result.get('js_minification_check'),
                result.get('css_minification_check'),
                result.get('mobile_responsiveness'),
            ]
            
            for check in checks:
                if check:
                    status = check.get('status', '')
                    total_checks += 1
                    if status == 'PASS':
                        passed_checks += 1
                    elif status == 'WARNING':
                        warning_checks += 1
                    elif status == 'FAIL':
                        failed_checks += 1
        
        # Calculate score: PASS = 100%, WARNING = 50%, FAIL = 0%
        if total_checks > 0:
            score = round(((passed_checks * 100 + warning_checks * 50) / total_checks))
        else:
            score = 0
        
        return score
