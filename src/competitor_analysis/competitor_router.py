"""
Competitor Analysis Router
API endpoints for competitor analysis
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_user
from src.core.subscription import require_pro_subscription
from src.models.user import User
from src.competitor_analysis.competitor_repository import CompetitorAnalysisRepository
from src.competitor_analysis.competitor_service import CompetitorAnalysisService
from src.competitor_analysis.competitor_controller import CompetitorAnalysisController
from src.competitor_analysis.schemas import (
    CompetitorAnalysisRequest,
    CompetitorAnalysisResponse,
    CompetitorAnalysisList,
    ExportFormat
)

router = APIRouter(prefix="/competitor-analysis", tags=["Competitor Analysis"])


def get_competitor_controller(db: AsyncSession = Depends(get_db)) -> CompetitorAnalysisController:
    """Dependency to get competitor analysis controller"""
    repo = CompetitorAnalysisRepository(db)
    service = CompetitorAnalysisService(repo)
    return CompetitorAnalysisController(service)


@router.post("/analyze", dependencies=[Depends(require_pro_subscription)])
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    current_user: User = Depends(get_current_user),
    controller: CompetitorAnalysisController = Depends(get_competitor_controller)
):
    """
    Analyze competitors (PRO FEATURE)
    
    Compare your website with a competitor across multiple SEO metrics.
    
    **Modes:**
    - `QUICK`: Homepage-only analysis (10-20s) - Ultra fast snapshot
    - `SITEMAP_ONLY`: Up to 100 pages from XML sitemap (20-40s)
    - `FULL_CRAWL`: Up to 100 pages discovered by crawling (30-90s)
    
    **Authentication:** Required. Pro subscription required.
    """
    return await controller.analyze_competitors(request, str(current_user.id))


@router.get("/history", dependencies=[Depends(require_pro_subscription)])
async def get_analysis_history(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    current_user: User = Depends(get_current_user),
    controller: CompetitorAnalysisController = Depends(get_competitor_controller)
):
    """
    Get competitor analysis history (PRO FEATURE)
    
    Retrieve all competitor analyses performed by the authenticated user.
    Requires Pro subscription.
    """
    return await controller.get_user_analyses(str(current_user.id), skip, limit)


@router.get("/{analysis_id}", dependencies=[Depends(require_pro_subscription)])
async def get_analysis(
    analysis_id: str = Path(..., description="Analysis ID"),
    current_user: User = Depends(get_current_user),
    controller: CompetitorAnalysisController = Depends(get_competitor_controller)
):
    """
    Get analysis by ID (PRO FEATURE)
    
    Retrieve a specific competitor analysis by its ID.
    Requires Pro subscription.
    """
    return await controller.get_analysis(analysis_id, str(current_user.id))


@router.delete("/{analysis_id}", dependencies=[Depends(require_pro_subscription)])
async def delete_analysis(
    analysis_id: str = Path(..., description="Analysis ID to delete"),
    current_user: User = Depends(get_current_user),
    controller: CompetitorAnalysisController = Depends(get_competitor_controller)
):
    """
    Delete an analysis (PRO FEATURE)
    
    Delete a competitor analysis. Only the owner can delete their analyses.
    Requires Pro subscription.
    """
    return await controller.delete_analysis(str(current_user.id), analysis_id)


@router.get("/{analysis_id}/export", dependencies=[Depends(require_pro_subscription)])
async def export_analysis(
    analysis_id: str = Path(..., description="Analysis ID"),
    format: ExportFormat = Query(ExportFormat.JSON, description="Export format"),
    current_user: User = Depends(get_current_user),
    controller: CompetitorAnalysisController = Depends(get_competitor_controller)
):
    """
    Export analysis results (PRO FEATURE)
    
    Export competitor analysis results in various formats.
    
    **Formats:**
    - `json`: Full data in JSON format
    - `csv`: Metrics comparison in CSV format
    - `pdf`: Formatted report (PDF)
    
    Requires Pro subscription.
    """
    # TODO: Implement export functionality
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Export functionality coming soon"
    )
