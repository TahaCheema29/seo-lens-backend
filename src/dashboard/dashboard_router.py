from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.dashboard.dashboard_service import DashboardService
from src.dashboard.dashboard_controller import DashboardController
from src.dashboard.schemas import DashboardOverviewResponse


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_controller(db: AsyncSession = Depends(get_db)) -> DashboardController:
    """Dependency to get dashboard controller"""
    service = DashboardService(db)
    return DashboardController(service)


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get dashboard overview with KPIs and recent analyses"""
    return await controller.get_overview(str(current_user.id))


@router.get("/analyses")
async def get_seo_analyses(
    current_user: User = Depends(get_current_user),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get user's SEO analyses"""
    return await controller.get_seo_analyses(str(current_user.id))


@router.get("/analyses/stats")
async def get_seo_analyses_stats(
    current_user: User = Depends(get_current_user),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get SEO analyses stats"""
    return await controller.get_seo_analyses_stats(str(current_user.id))


@router.get("/keywords")
async def get_keywords(
    current_user: User = Depends(get_current_user),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get user's keyword suggestions"""
    return await controller.get_keywords(str(current_user.id))


@router.get("/keywords/stats")
async def get_keywords_stats(
    current_user: User = Depends(get_current_user),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get keyword stats"""
    return await controller.get_keywords_stats(str(current_user.id))


@router.get("/ranks")
async def get_ranks(
    current_user: User = Depends(get_current_user),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get user's rank checks"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[SECURITY] User {current_user.id} ({current_user.email}) requesting /dashboard/ranks")
    return await controller.get_ranks(str(current_user.id))


@router.get("/ranks/stats")
async def get_ranks_stats(
    current_user: User = Depends(get_current_user),
    controller: DashboardController = Depends(get_dashboard_controller)
):
    """Get rank stats"""
    return await controller.get_ranks_stats(str(current_user.id))