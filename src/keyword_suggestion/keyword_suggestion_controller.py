from typing import List
from fastapi import HTTPException, status
from src.keyword_suggestion.repository.keyword_suggestion_repository import KeywordSuggestionRepository
from src.keyword_suggestion.keyword_suggestion_service import KeywordSuggestionService
from src.keyword_suggestion.schemas.keyword_suggestion import KeywordSuggestionResponse, KeywordSuggestionList
from src.seo_tools.schemas.suggest_keywords import SuggestKeywordResult
from src.models.keyword_suggestion import KeywordSuggestion
from src.core.response_status import RESPONSE_STATUS_ERROR


class KeywordSuggestionController:
    """Controller for keyword suggestion operations"""
    
    def __init__(self, service: KeywordSuggestionService):
        self.service = service
    
    async def analyze_and_save(
        self,
        user_id: str,
        keywords: List[str],
        save_result: bool = True
    ) -> dict:
        """Analyze keywords and save results"""
        result = await self.service.analyze_and_save(user_id, keywords, save_result)
        
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
                "items": [KeywordSuggestionResponse.model_validate(item) for item in data["items"]]
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
            "data": KeywordSuggestionResponse.model_validate(result["data"])
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