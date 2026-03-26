from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from statistics import mean
from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.models.seo_insight import SeoInsightResult
from src.seo_insight.repository.seo_insight_repository import SeoInsightRepository
from src.seo_insight.seo_insight_service import SeoInsightService
from src.seo_insight.seo_insight_controller import SeoInsightController
from src.seo_insight.schemas.seo_insight import SeoInsightResultResponse, SeoInsightResultList
from src.seo_tools.schemas.analyze_site_seo import AnalyzeSiteSeoRequest
from src.core.metrics import compute_seo_base_url_checks_metrics
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS


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
    controller: SeoInsightController = Depends(get_seo_insight_controller)
):
    """Analyze site SEO and optionally save result"""
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


@router.get("/stats")
async def seo_insight_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregated stats for dashboard cards.
    Derived from stored SEO checks in `base_url_checks`.
    """
    result = await db.execute(
        select(SeoInsightResult).where(SeoInsightResult.user_id == str(current_user.id))
    )
    items = result.scalars().all()

    if not items:
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="SEO insight stats retrieved successfully",
            data={
                "avgScore": 0,
                "totalCritical": 0,
                "totalWarnings": 0,
                "completedCount": 0,
                "processingCount": 0,
                "failedCount": 0,
            },
        )

    scores = []
    total_critical = 0
    total_warnings = 0

    completed = 0
    processing = 0
    failed = 0

    for item in items:
        metrics = compute_seo_base_url_checks_metrics(item.base_url_checks)
        scores.append(metrics["score"])
        total_critical += metrics["criticalIssues"]
        total_warnings += metrics["warnings"]

        if item.status == "completed":
            completed += 1
        elif item.status == "processing":
            processing += 1
        elif item.status == "failed":
            failed += 1
        else:
            completed += 1

    avg_score = float(mean(scores)) if scores else 0.0

    return create_response(
        status=RESPONSE_STATUS_SUCCESS,
        message="SEO insight stats retrieved successfully",
        data={
            "avgScore": avg_score,
            "totalCritical": total_critical,
            "totalWarnings": total_warnings,
            "completedCount": completed,
            "processingCount": processing,
            "failedCount": failed,
        },
    )