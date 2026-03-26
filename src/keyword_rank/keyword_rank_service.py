from typing import List
from src.keyword_rank.repository.keyword_rank_repository import KeywordRankRepository
from src.models.keyword_rank import KeywordRankResult
from src.seo_tools.utils.analyze_keyword_rank import KeywordRankChecker
from src.seo_tools.schemas.analyze_keyword_rank import AnalyzeKeywordRankResult
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS, RESPONSE_STATUS_ERROR


class KeywordRankService:
    """Service for keyword rank operations"""
    
    def __init__(self, repo: KeywordRankRepository):
        self.repo = repo
    
    async def analyze(
        self,
        target_url: str,
        keywords: List[str]
    ) -> List[AnalyzeKeywordRankResult]:
        """Analyze keyword rankings"""
        checker = KeywordRankChecker(headless=True)
        results = await checker.run(
            keywords=keywords,
            target_domain=target_url,
            max_results=100
        )
        return results
    
    async def analyze_and_save(
        self,
        user_id: str,
        target_url: str,
        keywords: List[str],
        save_result: bool = True
    ) -> dict:
        """Analyze keywords and save results"""
        try:
            results = await self.analyze(target_url, keywords)
            
            if save_result and results:
                for result in results:
                    result_dict = result.model_dump()
                    db_result = KeywordRankResult(
                        user_id=user_id,
                        target_url=target_url,
                        keywords=keywords,
                        keyword=result_dict.get("keyword"),
                        target_domain=result_dict.get("target_domain"),
                        target_position=result_dict.get("target_position"),
                        total_results=result_dict.get("total_results"),
                        search_results=[r.model_dump() if hasattr(r, 'model_dump') else r for r in result_dict.get("search_results", [])],
                        timestamp=result_dict.get("timestamp"),
                        date=result_dict.get("date"),
                    )
                    await self.repo.create(db_result)
            
            return create_response(
                status=RESPONSE_STATUS_SUCCESS,
                message="Keyword ranking analysis completed successfully",
                data=results
            )
        except Exception as e:
            return create_response(
                status=RESPONSE_STATUS_ERROR,
                message=f"Failed to analyze keyword rankings: {str(e)}",
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