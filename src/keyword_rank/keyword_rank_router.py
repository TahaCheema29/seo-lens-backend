from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.keyword_rank.repository.keyword_rank_repository import KeywordRankRepository
from src.keyword_rank.keyword_rank_service import KeywordRankService
from src.keyword_rank.keyword_rank_controller import KeywordRankController
from src.keyword_rank.schemas.keyword_rank import KeywordRankResultResponse, KeywordRankResultList
from src.seo_tools.schemas.analyze_keyword_rank import AnalyzeKeywordRankRequest, AnalyzeKeywordRankResult


router = APIRouter(prefix="/keyword-rank", tags=["Keyword Rank"])


def get_keyword_rank_controller(db: AsyncSession = Depends(get_db)) -> KeywordRankController:
    """Dependency to get keyword rank controller"""
    repo = KeywordRankRepository(db)
    service = KeywordRankService(repo)
    return KeywordRankController(service)


@router.post("/analyze")
async def analyze_keyword_rank(
    request: AnalyzeKeywordRankRequest,
    save_result: bool = Query(True, description="Whether to save result to database"),
    current_user: User = Depends(get_current_user),
    controller: KeywordRankController = Depends(get_keyword_rank_controller)
):
    """Analyze keyword ranking and optionally save result"""
    return await controller.analyze_and_save(
        user_id=str(current_user.id),
        target_url=str(request.url),
        keywords=request.keywords,
        save_result=save_result
    )


@router.get("/results")
async def get_keyword_rank_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    controller: KeywordRankController = Depends(get_keyword_rank_controller)
):
    """Get all keyword rank results for the current user"""
    return await controller.get_results(str(current_user.id), skip, limit)


@router.get("/results/{result_id}")
async def get_keyword_rank_result(
    result_id: str,
    current_user: User = Depends(get_current_user),
    controller: KeywordRankController = Depends(get_keyword_rank_controller)
):
    """Get a specific keyword rank result"""
    return await controller.get_result(str(current_user.id), result_id)


@router.delete("/results/{result_id}")
async def delete_keyword_rank_result(
    result_id: str,
    current_user: User = Depends(get_current_user),
    controller: KeywordRankController = Depends(get_keyword_rank_controller)
):
    """Delete a keyword rank result"""
    return await controller.delete_result(str(current_user.id), result_id)