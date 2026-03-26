from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.keyword_suggestion.repository.keyword_suggestion_repository import KeywordSuggestionRepository
from src.keyword_suggestion.keyword_suggestion_service import KeywordSuggestionService
from src.keyword_suggestion.keyword_suggestion_controller import KeywordSuggestionController
from src.keyword_suggestion.schemas.keyword_suggestion import KeywordSuggestionResponse, KeywordSuggestionList
from src.seo_tools.schemas.suggest_keywords import SuggestKeywordRequest, SuggestKeywordResult


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