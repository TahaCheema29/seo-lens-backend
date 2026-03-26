from src.admin.analytics.analytics_repository import AnalyticsRepository
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS


class AnalyticsService:
    """Service for admin analytics operations"""
    
    def __init__(self, repo: AnalyticsRepository):
        self.repo = repo
    
    async def get_overview(self) -> dict:
        """Get admin dashboard overview stats"""
        total_users = await self.repo.get_total_users()
        active_users = await self.repo.get_active_users()
        new_this_week = await self.repo.get_new_users_this_week()
        admin_count = await self.repo.get_admin_count()
        user_growth = await self.repo.get_user_growth_data()
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Admin overview retrieved successfully",
            data={
                "total_users": total_users,
                "active_users": active_users,
                "new_this_week": new_this_week,
                "admin_count": admin_count,
                "user_growth": user_growth
            }
        )
    
    async def get_analytics(self) -> dict:
        """Get platform analytics"""
        seo_analyses_total = await self.repo.get_seo_analyses_total()
        keyword_research_total = await self.repo.get_keyword_research_total()
        rank_checks_total = await self.repo.get_rank_checks_total()
        daily_active_users = await self.repo.get_daily_active_users()
        platform_usage = await self.repo.get_platform_usage()
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Analytics retrieved successfully",
            data={
                "seo_analyses_total": seo_analyses_total,
                "keyword_research_total": keyword_research_total,
                "rank_checks_total": rank_checks_total,
                "daily_active_users": daily_active_users,
                "platform_usage": platform_usage
            }
        )