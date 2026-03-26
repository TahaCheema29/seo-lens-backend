from typing import Optional
from fastapi import HTTPException, status
from src.seo_insight.repository.seo_insight_repository import SeoInsightRepository
from src.seo_insight.seo_insight_service import SeoInsightService
from src.seo_insight.schemas.seo_insight import SeoInsightResultResponse, SeoInsightResultList, SeoInsightStatsResponse
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoResponse
from src.models.seo_insight import SeoInsightResult
from src.core.response_status import RESPONSE_STATUS_ERROR


class SeoInsightController:
    """Controller for SEO insight operations"""
    
    def __init__(self, service: SeoInsightService):
        self.service = service
    
    async def analyze_and_save(
        self,
        user_id: str,
        target_url: str,
        crawl_mode: str,
        crawl_id: Optional[str] = None,
        save_result: bool = True
    ) -> dict:
        """Analyze site SEO and save results"""
        result = await self.service.analyze_and_save(user_id, target_url, crawl_mode, crawl_id, save_result)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return result
    
    async def get_results(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> dict:
        """Get all results for user"""
        result = await self.service.get_by_user(user_id, skip, limit)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        data = result["data"]
        return {
            "status": result["status"],
            "message": result["message"],
            "data": {
                "total": data["total"],
                "items": [SeoInsightResultResponse.model_validate(item) for item in data["items"]]
            }
        }
    
    async def get_result(self, user_id: str, result_id: str) -> dict:
        """Get specific result"""
        result = await self.service.get_by_id(user_id, result_id)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return {
            "status": result["status"],
            "message": result["message"],
            "data": SeoInsightResultResponse.model_validate(result["data"])
        }
    
    async def delete_result(self, user_id: str, result_id: str) -> dict:
        """Delete result"""
        result = await self.service.delete(user_id, result_id)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result
    
    async def get_stats(self, user_id: str) -> dict:
        """Get SEO insight statistics"""
        result = await self.service.get_stats(user_id)
        
        if result["status"] == RESPONSE_STATUS_ERROR:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return result