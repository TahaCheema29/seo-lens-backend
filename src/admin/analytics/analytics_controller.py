from src.admin.analytics.analytics_service import AnalyticsService


class AnalyticsController:
    """Controller for admin analytics operations"""
    
    def __init__(self, service: AnalyticsService):
        self.service = service
    
    async def get_overview(self) -> dict:
        """Get admin dashboard overview"""
        return await self.service.get_overview()
    
    async def get_analytics(self) -> dict:
        """Get platform analytics"""
        return await self.service.get_analytics()