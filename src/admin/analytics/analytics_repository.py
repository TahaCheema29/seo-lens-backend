from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from src.models.user import User, UserRole
from src.models.seo_insight import SeoInsightResult
from src.models.keyword_suggestion import KeywordSuggestion
from src.models.keyword_rank import KeywordRankResult
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS


class AnalyticsRepository:
    """Repository for admin analytics operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_total_users(self) -> int:
        """Get total user count"""
        result = await self.session.execute(
            select(func.count()).select_from(User)
        )
        return result.scalar() or 0
    
    async def get_active_users(self) -> int:
        """Get active user count"""
        result = await self.session.execute(
            select(func.count()).where(User.is_active == True)
        )
        return result.scalar() or 0
    
    async def get_new_users_this_week(self) -> int:
        """Get new users this week"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.session.execute(
            select(func.count()).where(User.created_at >= week_ago)
        )
        return result.scalar() or 0
    
    async def get_admin_count(self) -> int:
        """Get admin user count"""
        result = await self.session.execute(
            select(func.count()).where(User.role == UserRole.ADMIN)
        )
        return result.scalar() or 0
    
    async def get_seo_analyses_total(self) -> int:
        """Get total SEO analyses count"""
        result = await self.session.execute(
            select(func.count()).select_from(SeoInsightResult)
        )
        return result.scalar() or 0
    
    async def get_keyword_research_total(self) -> int:
        """Get total keyword research count"""
        result = await self.session.execute(
            select(func.count()).select_from(KeywordSuggestion)
        )
        return result.scalar() or 0
    
    async def get_rank_checks_total(self) -> int:
        """Get total rank checks count"""
        result = await self.session.execute(
            select(func.count()).select_from(KeywordRankResult)
        )
        return result.scalar() or 0
    
    async def get_user_growth_data(self) -> List[Dict[str, Any]]:
        """Get user growth data for last 6 months"""
        # For now, return mock data as we need historical aggregation
        # In production, this would query user created_at by month
        return [
            {"label": "Jan", "value": 120, "color": "#3b82f6"},
            {"label": "Feb", "value": 145, "color": "#3b82f6"},
            {"label": "Mar", "value": 180, "color": "#3b82f6"},
            {"label": "Apr", "value": 210, "color": "#3b82f6"},
            {"label": "May", "value": 248, "color": "#3b82f6"},
            {"label": "Jun", "value": 290, "color": "#3b82f6"},
        ]
    
    async def get_daily_active_users(self) -> List[Dict[str, Any]]:
        """Get daily active users for last 7 days"""
        # For now, return mock data as we need user activity tracking
        # In production, this would query user login/history tables
        return [
            {"date": "Mon", "count": 45},
            {"date": "Tue", "count": 52},
            {"date": "Wed", "count": 38},
            {"date": "Thu", "count": 65},
            {"date": "Fri", "count": 48},
            {"date": "Sat", "count": 22},
            {"date": "Sun", "count": 18},
        ]
    
    async def get_platform_usage(self) -> List[Dict[str, Any]]:
        """Get platform usage breakdown"""
        seo_total = await self.get_seo_analyses_total()
        keyword_total = await self.get_keyword_research_total()
        rank_total = await self.get_rank_checks_total()
        
        return [
            {"label": "SEO Analyses", "value": seo_total, "color": "#8b5cf6"},
            {"label": "Keyword Research", "value": keyword_total, "color": "#10b981"},
            {"label": "Rank Checks", "value": rank_total, "color": "#f59e0b"}
        ]