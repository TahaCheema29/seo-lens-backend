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
        total_analyses = await self.repo.get_seo_analyses_total()
        total_keywords = await self.repo.get_keyword_research_total()
        total_rank_checks = await self.repo.get_rank_checks_total()
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Admin overview retrieved successfully",
            data={
                "total_users": total_users,
                "active_users": active_users,
                "total_analyses": total_analyses,
                "total_keywords": total_keywords,
                "total_rank_checks": total_rank_checks
            }
        )
    
    async def get_analytics(self) -> dict:
        """Get platform analytics"""
        # Get counts by status from database
        seo_stats = await self.repo.get_seo_analyses_stats()
        keyword_stats = await self.repo.get_keyword_research_stats()
        rank_stats = await self.repo.get_rank_checks_stats()
        
        # Get daily active users data
        daily_active_users = await self.repo.get_daily_active_users()
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Analytics retrieved successfully",
            data={
                "seo_analyses": {
                    "total": seo_stats["total"],
                    "completed": seo_stats["completed"],
                    "processing": seo_stats["processing"]
                },
                "keyword_research": {
                    "total": keyword_stats["total"],
                    "completed": keyword_stats["completed"],
                    "processing": keyword_stats["processing"]
                },
                "rank_checks": {
                    "total": rank_stats["total"],
                    "completed": rank_stats["completed"],
                    "processing": rank_stats["processing"]
                },
                "user_activity": {
                    "daily_active_users": [d["count"] for d in daily_active_users],
                    "labels": [d["date"] for d in daily_active_users]
                }
            }
        )