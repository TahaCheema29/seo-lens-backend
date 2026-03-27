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
    
    async def get_seo_analyses(self, user_id: str) -> dict:
        """Get user's SEO analyses"""
        return await self.service.get_seo_analyses(user_id)
    
    async def get_seo_analyses_stats(self, user_id: str) -> dict:
        """Get SEO analyses stats"""
        return await self.service.get_seo_analyses_stats(user_id)
    
    async def get_keywords(self, user_id: str) -> dict:
        """Get user's keyword suggestions"""
        return await self.service.get_keywords(user_id)
    
    async def get_keywords_stats(self, user_id: str) -> dict:
        """Get keyword stats"""
        return await self.service.get_keywords_stats(user_id)
    
    async def get_ranks(self, user_id: str) -> dict:
        """Get user's rank checks"""
        return await self.service.get_ranks(user_id)
    
    async def get_ranks_stats(self, user_id: str) -> dict:
        """Get rank stats"""
        return await self.service.get_ranks_stats(user_id)