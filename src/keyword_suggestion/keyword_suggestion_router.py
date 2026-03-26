from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from statistics import mean
from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.keyword_suggestion import KeywordSuggestion
from src.keyword_suggestion.repository.keyword_suggestion_repository import KeywordSuggestionRepository
from src.keyword_suggestion.keyword_suggestion_service import KeywordSuggestionService
from src.keyword_suggestion.keyword_suggestion_controller import KeywordSuggestionController
from src.keyword_suggestion.schemas.keyword_suggestion import KeywordSuggestionResponse, KeywordSuggestionList
from src.seo_tools.schemas.suggest_keywords import SuggestKeywordRequest, SuggestKeywordResult
from src.core.metrics import compute_keyword_suggestion_metrics
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS


router = APIRouter(prefix="/keyword-suggestion", tags=["Keyword Suggestion"])


def get_keyword_suggestion_controller(db: AsyncSession = Depends(get_db)) -> KeywordSuggestionController:
    """Dependency to get keyword suggestion controller"""
    repo = KeywordSuggestionRepository(db)
    service = KeywordSuggestionService(repo)
    return KeywordSuggestionController(service)


@router.post("/analyze")
async def analyze_keyword_suggestion(
    request: SuggestKeywordRequest,
    save_result: bool = Query(True, description="Whether to save result to database"),
    current_user: User = Depends(get_current_user),
    controller: KeywordSuggestionController = Depends(get_keyword_suggestion_controller)
):
    """Analyze keyword suggestions and optionally save result"""
    return await controller.analyze_and_save(
        user_id=str(current_user.id),
        keywords=request.keywords,
        save_result=save_result
    )


@router.get("/results")
async def get_keyword_suggestions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    controller: KeywordSuggestionController = Depends(get_keyword_suggestion_controller)
):
    """Get all keyword suggestions for the current user"""
    return await controller.get_results(str(current_user.id), skip, limit)


@router.get("/results/{result_id}")
async def get_keyword_suggestion(
    result_id: str,
    current_user: User = Depends(get_current_user),
    controller: KeywordSuggestionController = Depends(get_keyword_suggestion_controller)
):
    """Get a specific keyword suggestion result"""
    return await controller.get_result(str(current_user.id), result_id)


@router.delete("/results/{result_id}")
async def delete_keyword_suggestion(
    result_id: str,
    current_user: User = Depends(get_current_user),
    controller: KeywordSuggestionController = Depends(get_keyword_suggestion_controller)
):
    """Delete a keyword suggestion result"""
    return await controller.delete_result(str(current_user.id), result_id)


@router.get("/stats")
async def keyword_suggestion_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated stats for dashboard cards (keyword suggestion)."""
    result = await db.execute(
        select(KeywordSuggestion).where(KeywordSuggestion.user_id == str(current_user.id))
    )
    items = result.scalars().all()

    if not items:
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Keyword suggestion stats retrieved successfully",
            data={
                "totalKeywords": 0,
                "completedCount": 0,
                "processingCount": 0,
                "avgRelatedKeywords": 0,
            },
        )

    related_counts = []
    completed = 0
    processing = 0

    for item in items:
        metrics = compute_keyword_suggestion_metrics(
            related_searches=item.related_searches,
            long_tail_keywords=item.long_tail_keywords,
            search_results=item.search_results,
        )
        related_counts.append(metrics["relatedKeywordsCount"])

        if item.status == "completed":
            completed += 1
        elif item.status == "processing":
            processing += 1
        else:
            completed += 1

    avg_related = float(mean(related_counts)) if related_counts else 0.0

    return create_response(
        status=RESPONSE_STATUS_SUCCESS,
        message="Keyword suggestion stats retrieved successfully",
        data={
            "totalKeywords": len(items),
            "completedCount": completed,
            "processingCount": processing,
            "avgRelatedKeywords": avg_related,
        },
    )