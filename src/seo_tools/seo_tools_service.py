import time
import uuid
from typing import Optional, List
from datetime import datetime
from src.config.redis_client import redis_client
from src.config.logger_config import setup_logger
from src.config.database import get_db_session
from src.seo_tools.utils.analyze_keyword_rank import KeywordRankChecker
from src.seo_tools.schemas.analyze_keyword_rank import AnalyzeKeywordRankRequest
from src.seo_tools.utils.suggest_keyword import KeywordResearch
from src.seo_tools.schemas.suggest_keywords import SuggestKeywordRequest
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoRequest, AnalyzeSiteSeoResponse
from src.seo_tools.utils.seo_crawler import SEOCrawler, URLStatus
from src.seo_tools.utils.seo_scraper import SEOScraper
from src.models.seo_insight import SeoInsightResult
from src.models.keyword_rank import KeywordRankResult
from src.models.keyword_suggestion import KeywordSuggestion
from src.models.enums import AnalysisStatus


class SeoToolsService:

    def __init__(self):
        self.logger = setup_logger(__name__)
            
    async def analyze_keyword_rank(self, user_input: AnalyzeKeywordRankRequest, user_id: str = None):
        
        checker = KeywordRankChecker(headless=True)
        print("Starting keyword rank checking...")
        results = await checker.run(
            keywords=user_input.keywords,
            target_domain=str(user_input.url),
            max_results=100
        )

        print(results)
        
        # Save to database if user is authenticated
        if user_id and results:
            await self._save_keyword_rank_results(user_id, str(user_input.url), user_input.keywords, results)
        
        return results
    

    async def suggest_keywords(self, user_input: SuggestKeywordRequest, user_id: str = None):
        
        researcher = KeywordResearch(headless=True)
        print("Starting keyword research...")
        results = await researcher.run(user_input.keywords)
        
        # Save to database if user is authenticated
        if user_id and results:
            await self._save_keyword_suggestions(user_id, user_input.keywords, results)
        
        return results
    

    async def analyze_site_seo(self, user_input: AnalyzeSiteSeoRequest, user_id: str = None, crawl_id: Optional[str] = None) -> AnalyzeSiteSeoResponse:
      
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

            # Save to database if user is authenticated
            if user_id:
                await self._save_seo_insight(user_id, str(user_input.url), user_input.crawl_mode, results)

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

    async def _save_seo_insight(self, user_id: str, target_url: str, crawl_mode: str, results: AnalyzeSiteSeoResponse):
        """Save SEO analysis results to database"""
        try:
            async with get_db_session() as db:
                # Calculate average response time
                avg_response_time = None
                if results.url_results:
                    response_times = [r.response_time_ms for r in results.url_results if r.response_time_ms]
                    if response_times:
                        avg_response_time = sum(response_times) / len(response_times)
                
                # Convert to JSON-serializable dict with mode='json' to handle HttpUrl types
                import json
                base_checks_dict = json.loads(results.base_url_checks.model_dump_json())
                url_results_list = [json.loads(r.model_dump_json()) for r in results.url_results]
                
                # Calculate SEO score based on base_url_checks and url_results
                score = self._calculate_seo_score(base_checks_dict, url_results_list)
                
                # Convert crawl_mode enum to string if needed
                crawl_mode_str = crawl_mode.value if hasattr(crawl_mode, 'value') else str(crawl_mode)
                
                seo_result = SeoInsightResult(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(user_id),
                    target_url=target_url,
                    crawl_mode=crawl_mode_str,
                    base_url_checks=base_checks_dict,
                    url_results=url_results_list,
                    total_pages=len(results.url_results),
                    avg_response_time_ms=avg_response_time,
                    score=score,
                    status=AnalysisStatus.COMPLETED
                )
                db.add(seo_result)
                await db.commit()
                self.logger.info(f"Saved SEO insight result for user {user_id} with score {score}")
        except Exception as e:
            self.logger.error(f"Error saving SEO insight: {e}", exc_info=True)
            # Don't raise - we don't want to fail the request if saving fails
    
    def _calculate_seo_score(self, base_checks: dict, url_results: list = None) -> int:
        """Calculate SEO score matching frontend logic:
        PASS = 100%, WARNING = 50%, FAIL = 0%
        """
        if not base_checks:
            return 0
        
        total_checks = 0
        passed_checks = 0
        warning_checks = 0
        failed_checks = 0
        
        # Define base URL checks (same as frontend)
        base_check_keys = [
            'www_redirect_check',
            'robots_txt_check', 
            'https_ssl_check',
            'directory_listing_check',
            'expires_headers_check',
            'caching_advice'
        ]
        
        # Count base URL checks
        for key in base_check_keys:
            check = base_checks.get(key)
            if check:
                total_checks += 1
                if isinstance(check, dict):
                    status = check.get('status', '')
                    if status == 'PASS':
                        passed_checks += 1
                    elif status == 'WARNING':
                        warning_checks += 1
                    elif status == 'FAIL':
                        failed_checks += 1
                elif check == True:
                    passed_checks += 1
                elif check == False:
                    failed_checks += 1
        
        # Count URL result checks if provided
        if url_results:
            url_check_keys = [
                'title_length_check',
                'title_keyword_presence',
                'meta_description_length_check',
                'meta_description_keyword_presence',
                'h1_check',
                'image_alt_check',
                'canonical_check',
                'noindex_check',
                'open_graph_check',
                'schema_validation',
                'html_size_check',
                'response_time_check',
                'js_minification_check',
                'css_minification_check',
                'mobile_responsiveness'
            ]
            
            for result in url_results:
                for key in url_check_keys:
                    check = result.get(key) if isinstance(result, dict) else getattr(result, key, None)
                    if check:
                        total_checks += 1
                        if isinstance(check, dict):
                            status = check.get('status', '')
                            if status == 'PASS':
                                passed_checks += 1
                            elif status == 'WARNING':
                                warning_checks += 1
                            elif status == 'FAIL':
                                failed_checks += 1
                        elif check == True:
                            passed_checks += 1
                        elif check == False:
                            failed_checks += 1
        
        if total_checks == 0:
            return 0
        
        # Calculate score: PASS = 100%, WARNING = 50%, FAIL = 0%
        # Match frontend formula: Math.round(((passed * 100 + warning * 50) / total))
        score = round((passed_checks * 100 + warning_checks * 50) / total_checks)
        return score

    async def _save_keyword_rank_results(self, user_id: str, target_url: str, keywords: List[str], results):
        """Save keyword rank results to database"""
        try:
            import json
            async with get_db_session() as db:
                for result in results:
                    # Convert Pydantic model to dict if needed
                    if hasattr(result, 'model_dump'):
                        result_dict = result.model_dump()
                    elif hasattr(result, 'dict'):
                        result_dict = result.dict()
                    else:
                        result_dict = result
                    
                    # Ensure search_results is JSON serializable
                    search_results = result_dict.get("search_results", [])
                    if search_results:
                        # Convert any HttpUrl or other non-serializable types to strings
                        search_results = json.loads(json.dumps(search_results, default=str))
                    
                    rank_result = KeywordRankResult(
                        id=uuid.uuid4(),
                        user_id=uuid.UUID(user_id),
                        target_url=target_url,
                        keywords=keywords,
                        keyword=result_dict.get("keyword", ""),
                        target_domain=result_dict.get("target_domain"),
                        target_position=result_dict.get("target_position"),
                        total_results=result_dict.get("total_results", 0),
                        search_results=search_results,
                        timestamp=time.time(),
                        date=datetime.now().strftime("%Y-%m-%d"),
                        status=AnalysisStatus.COMPLETED
                    )
                    db.add(rank_result)
                await db.commit()
                self.logger.info(f"Saved {len(results)} keyword rank results for user {user_id}")
        except Exception as e:
            self.logger.error(f"Error saving keyword rank results: {e}", exc_info=True)
            # Don't raise - we don't want to fail the request if saving fails

    async def _save_keyword_suggestions(self, user_id: str, input_keywords: List[str], results):
        """Save keyword suggestion results to database"""
        try:
            import json
            async with get_db_session() as db:
                for result in results:
                    # Convert Pydantic model to dict if needed
                    if hasattr(result, 'model_dump'):
                        result_dict = result.model_dump()
                    elif hasattr(result, 'dict'):
                        result_dict = result.dict()
                    else:
                        result_dict = result
                    
                    # Ensure all list fields are JSON serializable
                    def make_serializable(data):
                        if isinstance(data, list):
                            return [make_serializable(item) for item in data]
                        elif isinstance(data, dict):
                            return {k: make_serializable(v) for k, v in data.items()}
                        else:
                            return str(data) if not isinstance(data, (str, int, float, bool, type(None))) else data
                    
                    suggestion = KeywordSuggestion(
                        id=uuid.uuid4(),
                        user_id=uuid.UUID(user_id),
                        primary_keyword=result_dict.get("keyword", input_keywords[0] if input_keywords else ""),
                        search_results=make_serializable(result_dict.get("search_results", [])),
                        related_searches=make_serializable(result_dict.get("related_searches", [])),
                        people_also_ask=make_serializable(result_dict.get("people_also_ask", [])),
                        autocomplete_suggestions=make_serializable(result_dict.get("autocomplete_suggestions", [])),
                        long_tail_keywords=make_serializable(result_dict.get("long_tail_keywords", [])),
                        total_related_terms=len(result_dict.get("related_searches", [])) + len(result_dict.get("long_tail_keywords", [])),
                        timestamp=time.time(),
                        date=datetime.now().strftime("%Y-%m-%d"),
                        status=AnalysisStatus.COMPLETED
                    )
                    db.add(suggestion)
                await db.commit()
                self.logger.info(f"Saved {len(results)} keyword suggestions for user {user_id}")
        except Exception as e:
            self.logger.error(f"Error saving keyword suggestions: {e}", exc_info=True)
            # Don't raise - we don't want to fail the request if saving fails
