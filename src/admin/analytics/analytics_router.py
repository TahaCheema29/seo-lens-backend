from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_admin
from src.models.user import Admin
from src.admin.analytics.analytics_repository import AnalyticsRepository
from src.admin.analytics.analytics_service import AnalyticsService
from src.admin.analytics.analytics_controller import AnalyticsController


router = APIRouter(prefix="/admin", tags=["Admin - Analytics"])


def get_analytics_controller(db: AsyncSession = Depends(get_db)) -> AnalyticsController:
    """Dependency to get analytics controller"""
    repo = AnalyticsRepository(db)
    service = AnalyticsService(repo)
    return AnalyticsController(service)


@router.get("/overview")
async def get_admin_overview(
    admin_user: Admin = Depends(get_current_admin),
    controller: AnalyticsController = Depends(get_analytics_controller)
):
    """Get admin dashboard overview (Admin only)"""
    return await controller.get_overview()


@router.get("/analytics")
async def get_admin_analytics(
    admin_user: Admin = Depends(get_current_admin),
    controller: AnalyticsController = Depends(get_analytics_controller)
):
    """Get platform analytics (Admin only)"""
    return await controller.get_analytics()