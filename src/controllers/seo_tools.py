from src.config.logger_config import setup_logger
from src.constants.response_status import RESPONSE_STATUS_SUCCESS,RESPONSE_STATUS_ERROR
from src.utils.response_helper import create_response
from src.services.seo_tools import SeoToolsService
from src.schemas.analyze_site_seo import AnalyzeSiteSeoRequest
from src.schemas.suggest_keywords import SuggestKeywordRequest
from src.schemas.analyze_keyword_rank import AnalyzeKeywordRankRequest


class SeoToolsController:
    
    def __init__(self):
        self.seo_tools_services = SeoToolsService()
        self.logger = setup_logger(__name__)


    async def analyze_keyword_rank(self,user_input:AnalyzeKeywordRankRequest):
        result=await self.seo_tools_services.analyze_keyword_rank(user_input)
        return create_response(RESPONSE_STATUS_SUCCESS,"Rank Checked Successfully completed",result)

    async def suggest_keywords(self,user_input:SuggestKeywordRequest):
        result=await self.seo_tools_services.suggest_keywords(user_input)
        return create_response(RESPONSE_STATUS_SUCCESS,"Suggested Keywords",result)


    async def analyze_site_seo(self, user_input: AnalyzeSiteSeoRequest, crawl_id: str = None):
        
        try:
            result = await self.seo_tools_services.analyze_site_seo(user_input, crawl_id=crawl_id)
            return create_response(RESPONSE_STATUS_SUCCESS, "Seo Checks Successfully completed", result)
        except Exception as e:
            self.logger.error(f"Error in analyze_site_seo controller: {e}", exc_info=True)
            return create_response(
                RESPONSE_STATUS_ERROR, 
                f"Error during SEO analysis: {str(e)}", 
                None
            )
    
