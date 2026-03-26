from typing import List
from fastapi import HTTPException, status
from src.keyword_rank.repository.keyword_rank_repository import KeywordRankRepository
from src.keyword_rank.keyword_rank_service import KeywordRankService
from src.keyword_rank.schemas.keyword_rank import KeywordRankResultResponse, KeywordRankResultList
from src.seo_tools.schemas.analyze_keyword_rank import AnalyzeKeywordRankResult
from src.models.keyword_rank import KeywordRankResult
from src.core.response_status import RESPONSE_STATUS_ERROR


class KeywordRankController:
    """Controller for keyword rank operations"""
    
    def __init__(self, service: KeywordRankService):
        self.service = service
    
    async def analyze_and_save(
        self,
        user_id: str,
        target_url: str,
        keywords: List[str],
        save_result: bool = True
    ) -> dict:
        """Analyze keywords and save results"""
        result = await self.service.analyze_and_save(user_id, target_url, keywords, save_result)
        
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
                "items": [KeywordRankResultResponse.model_validate(item) for item in data["items"]]
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
            "data": KeywordRankResultResponse.model_validate(result["data"])
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