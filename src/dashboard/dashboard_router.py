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