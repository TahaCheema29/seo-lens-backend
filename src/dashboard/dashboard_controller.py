from sqlalchemy.ext.asyncio import AsyncSession
from src.dashboard.dashboard_service import DashboardService
from src.core.response_status import RESPONSE_STATUS_ERROR


class DashboardController:
    """Controller for dashboard operations"""
    
    def __init__(self, service: DashboardService):
        self.service = service
    
    async def get_overview(self, user_id: str) -> dict:
        """Get dashboard overview"""
        return await self.service.get_overview(user_id)