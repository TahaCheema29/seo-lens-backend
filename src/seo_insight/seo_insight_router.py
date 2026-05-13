from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.seo_insight.repository.seo_insight_repository import SeoInsightRepository
from src.seo_insight.seo_insight_service import SeoInsightService
from src.seo_insight.seo_insight_controller import SeoInsightController
from src.seo_insight.schemas.seo_insight import SeoInsightResultResponse, SeoInsightResultList, SeoInsightStatsResponse
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoRequest, CrawlMode
from src.billing.access import assert_active_pro


router = APIRouter(prefix="/seo-insight", tags=["SEO Insight"])


def get_seo_insight_controller(db: AsyncSession = Depends(get_db)) -> SeoInsightController:
    """Dependency to get SEO insight controller"""
    repo = SeoInsightRepository(db)
    service = SeoInsightService(repo)
    return SeoInsightController(service)


@router.post("/analyze")
async def analyze_seo_insight(
    request: AnalyzeSiteSeoRequest,
    save_result: bool = Query(True, description="Whether to save result to database"),
    crawl_id: str = Query(None, description="Crawl ID for live preview"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    controller: SeoInsightController = Depends(get_seo_insight_controller),
):
    """Analyze site SEO and optionally save result"""
    if request.crawl_mode == CrawlMode.FULL_CRAWL:
        await assert_active_pro(db, current_user.id)
    return await controller.analyze_and_save(
        user_id=str(current_user.id),
        target_url=str(request.url),
        crawl_mode=request.crawl_mode.value,
        crawl_id=crawl_id,
        save_result=save_result
    )


@router.get("/results")
async def get_seo_insight_results(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    controller: SeoInsightController = Depends(get_seo_insight_controller)
):
    """Get all SEO insight results for the current user"""
    return await controller.get_results(str(current_user.id), skip, limit)


@router.get("/stats", response_model=SeoInsightStatsResponse)
async def get_seo_insight_stats(
    current_user: User = Depends(get_current_user),
    controller: SeoInsightController = Depends(get_seo_insight_controller)
):
    """Get SEO insight statistics for the current user"""
    return await controller.get_stats(str(current_user.id))


@router.get("/results/{result_id}")
async def get_seo_insight_result(
    result_id: str,
    current_user: User = Depends(get_current_user),
    controller: SeoInsightController = Depends(get_seo_insight_controller)
):
    """Get a specific SEO insight result"""
    return await controller.get_result(str(current_user.id), result_id)


@router.delete("/results/{result_id}")
async def delete_seo_insight_result(
    result_id: str,
    current_user: User = Depends(get_current_user),
    controller: SeoInsightController = Depends(get_seo_insight_controller)
):
    """Delete an SEO insight result"""
    return await controller.delete_result(str(current_user.id), result_id)