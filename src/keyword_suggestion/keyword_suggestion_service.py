from typing import List
from src.keyword_suggestion.repository.keyword_suggestion_repository import KeywordSuggestionRepository
from src.models.keyword_suggestion import KeywordSuggestion
from src.seo_tools.utils.suggest_keyword import KeywordResearch
from src.seo_tools.schemas.suggest_keywords import SuggestKeywordResult
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class KeywordSuggestionService:
    """Service for keyword suggestion operations"""
    
    def __init__(self, repo: KeywordSuggestionRepository):
        self.repo = repo
    
    async def analyze(self, keywords: List[str]) -> List[SuggestKeywordResult]:
        """Analyze keyword suggestions"""
        researcher = KeywordResearch(headless=True)
        results = await researcher.run(keywords)
        return results
    
    async def analyze_and_save(
        self,
        user_id: str,
        keywords: List[str],
        save_result: bool = True
    ) -> dict:
        """Analyze keywords and save results"""
        try:
            results = await self.analyze(keywords)
            
            if save_result and results:
                for result in results:
                    result_dict = result.model_dump()
                    db_result = KeywordSuggestion(
                        user_id=user_id,
                        primary_keyword=result_dict.get("primary_keyword"),
                        search_results=[r.model_dump() if hasattr(r, 'model_dump') else r for r in result_dict.get("search_results", [])],
                        related_searches=result_dict.get("related_searches", []),
                        people_also_ask=[r.model_dump() if hasattr(r, 'model_dump') else r for r in result_dict.get("people_also_ask", [])],
                        autocomplete_suggestions=result_dict.get("autocomplete_suggestions", []),
                        long_tail_keywords=result_dict.get("long_tail_keywords", []),
                        total_related_terms=result_dict.get("total_related_terms", 0),
                        timestamp=result_dict.get("timestamp"),
                        date=result_dict.get("date"),
                    )
                    await self.repo.create(db_result)
            
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Keyword suggestion analysis completed successfully",
                data=results
            )
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to analyze keyword suggestions: {str(e)}",
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
    
    async def get_stats(self, user_id: str) -> dict:
        """Get statistics for user's keyword suggestions"""
        from src.models.keyword_suggestion import AnalysisStatus
        
        try:
            items = await self.repo.get_by_user(user_id, skip=0, limit=1000)
            
            total_keywords = len(items)
            completed_count = 0
            processing_count = 0
            failed_count = 0
            pending_count = 0
            
            total_related = 0
            total_long_tail = 0
            
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
                
                if item.related_searches:
                    total_related += len(item.related_searches)
                if item.long_tail_keywords:
                    total_long_tail += len(item.long_tail_keywords)
            
            avg_related = total_related / total_keywords if total_keywords > 0 else 0
            avg_long_tail = total_long_tail / total_keywords if total_keywords > 0 else 0
            
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Stats retrieved successfully",
                data={
                    "total_keywords": total_keywords,
                    "completed_count": completed_count,
                    "processing_count": processing_count,
                    "failed_count": failed_count,
                    "pending_count": pending_count,
                    "avg_related_keywords": round(avg_related, 2),
                    "avg_long_tail_keywords": round(avg_long_tail, 2)
                }
            )
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to get stats: {str(e)}",
                data=None
            )