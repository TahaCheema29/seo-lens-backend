from src.config.logger_config import setup_logger
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR
from src.core.response_helper import create_response
from src.seo_tools.seo_tools_service import SeoToolsService
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoRequest
from src.seo_tools.schemas.suggest_keywords import SuggestKeywordRequest
from src.seo_tools.schemas.analyze_keyword_rank import AnalyzeKeywordRankRequest
from src.seo_tools.schemas.competitor_analysis import CompetitorAnalysisRequest
from src.seo_tools.utils.competitor_analysis import run_competitor_analysis


class SeoToolsController:
    
    def __init__(self):
        self.seo_tools_services = SeoToolsService()
        self.logger = setup_logger(__name__)


    async def analyze_keyword_rank(self, user_input: AnalyzeKeywordRankRequest, user_id: str = None):
        result = await self.seo_tools_services.analyze_keyword_rank(user_input, user_id)
        return create_response(RESPONSE_STATUS_SUCCESS, "Rank Checked Successfully completed", result)

    async def suggest_keywords(self, user_input: SuggestKeywordRequest, user_id: str = None):
        result = await self.seo_tools_services.suggest_keywords(user_input, user_id)
        return create_response(RESPONSE_STATUS_SUCCESS, "Suggested Keywords", result)


    async def analyze_site_seo(self, user_input: AnalyzeSiteSeoRequest, user_id: str = None, crawl_id: str = None):
        
        try:
            result = await self.seo_tools_services.analyze_site_seo(user_input, user_id=user_id, crawl_id=crawl_id)
            return create_response(RESPONSE_STATUS_SUCCESS, "Seo Checks Successfully completed", result)
        except Exception as e:
            self.logger.error(f"Error in analyze_site_seo controller: {e}", exc_info=True)
            return create_response(
                RESPONSE_STATUS_ERROR, 
                f"Error during SEO analysis: {str(e)}", 
                None
            )

    async def analyze_competitor(self, user_input: CompetitorAnalysisRequest):
        try:
            import uuid, asyncio, json
            from src.config.redis_client import get_redis

            job_id = str(uuid.uuid4())
            redis = await get_redis()
            await redis.set(
                f"competitor_job:{job_id}",
                json.dumps({"status": "pending"}),
                ex=3600
            )

            async def run_and_store():
                try:
                    result = await run_competitor_analysis(user_input)
                    await redis.set(
                        f"competitor_job:{job_id}",
                        json.dumps({
                            "status": "complete",
                            "data": result.model_dump(mode="json")
                        }),
                        ex=3600
                    )
                except Exception as e:
                    self.logger.error(f"Background competitor job failed: {e}", exc_info=True)
                    await redis.set(
                        f"competitor_job:{job_id}",
                        json.dumps({"status": "failed", "error": str(e)}),
                        ex=3600
                    )

            asyncio.create_task(run_and_store())

            return create_response(
                RESPONSE_STATUS_SUCCESS,
                "Analysis started",
                {"jobId": job_id, "status": "pending"}
            )
        except Exception as e:
            self.logger.error(f"Error starting competitor analysis: {e}", exc_info=True)
            return create_response(RESPONSE_STATUS_ERROR, str(e), None)


    async def get_competitor_analysis_status(self, job_id: str):
        try:
            import json
            from src.config.redis_client import get_redis

            redis = await get_redis()
            raw = await redis.get(f"competitor_job:{job_id}")
            if not raw:
                return create_response(RESPONSE_STATUS_ERROR, "Job not found", None)

            job = json.loads(raw)
            return create_response(RESPONSE_STATUS_SUCCESS, "Job status", job)
        except Exception as e:
            self.logger.error(f"Error fetching job status: {e}", exc_info=True)
            return create_response(RESPONSE_STATUS_ERROR, str(e), None)