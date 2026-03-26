from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.seo_insight import SeoInsightResult
from src.models.keyword_suggestion import KeywordSuggestion
from src.models.keyword_rank import KeywordRankResult
from src.dashboard.schemas.dashboard_schema import (
    DashboardOverviewResponse,
    RecentAnalyses,
    RecentItem,
    PerformanceChartItem,
)
from src.core.response_helper import create_response
from src.core.response_status import RESPONSE_STATUS_SUCCESS


class DashboardService:
    """Service for dashboard operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_overview(self, user_id: str) -> dict:
        """Get dashboard overview for a user"""
        total_seo = await self._count_seo_insights(user_id)
        total_keywords = await self._count_keyword_suggestions(user_id)
        total_ranks = await self._count_keyword_ranks(user_id)
        
        avg_seo_score = await self._get_avg_seo_score(user_id)
        avg_position = await self._get_avg_position(user_id)
        
        recent_seo = await self._get_recent_seo_insights(user_id, limit=3)
        recent_keywords = await self._get_recent_keyword_suggestions(user_id, limit=3)
        recent_ranks = await self._get_recent_keyword_ranks(user_id, limit=3)
        
        performance_chart = await self._get_performance_chart(user_id)
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Dashboard overview retrieved successfully",
            data=DashboardOverviewResponse(
                seo_score=avg_seo_score,
                keywords_tracked=total_keywords,
                total_analyses=total_seo + total_keywords + total_ranks,
                performance_chart=performance_chart,
                recent_analyses=RecentAnalyses(
                    seo=recent_seo,
                    keywords=recent_keywords,
                    rank=recent_ranks
                ),
                stats={
                    "total_seo_analyses": total_seo,
                    "total_keyword_suggestions": total_keywords,
                    "total_keyword_ranks": total_ranks,
                    "avg_position": avg_position
                }
            ).model_dump()
        )
    
    async def _count_seo_insights(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).where(SeoInsightResult.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def _count_keyword_suggestions(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).where(KeywordSuggestion.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def _count_keyword_ranks(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).where(KeywordRankResult.user_id == user_id)
        )
        return result.scalar() or 0
    
    async def _get_avg_seo_score(self, user_id: str) -> float:
        result = await self.db.execute(
            select(SeoInsightResult).where(SeoInsightResult.user_id == user_id).limit(10)
        )
        insights = result.scalars().all()
        if not insights:
            return 0.0
        scores = []
        for insight in insights:
            if insight.base_url_checks:
                score = self._calculate_seo_score(insight.base_url_checks)
                scores.append(score)
        return sum(scores) / len(scores) if scores else 0.0
    
    def _calculate_seo_score(self, checks: dict) -> float:
        if not checks:
            return 0.0
        total_checks = len(checks)
        passed = sum(1 for k, v in checks.items() if v == True or (isinstance(v, dict) and v.get('passed')))
        return (passed / total_checks * 100) if total_checks else 0.0
    
    async def _get_avg_position(self, user_id: str) -> float:
        result = await self.db.execute(
            select(KeywordRankResult).where(
                KeywordRankResult.user_id == user_id,
                KeywordRankResult.target_position.isnot(None)
            )
        )
        ranks = result.scalars().all()
        if not ranks:
            return 0.0
        positions = [r.target_position for r in ranks if r.target_position]
        return sum(positions) / len(positions) if positions else 0.0
    
    async def _get_recent_seo_insights(self, user_id: str, limit: int = 3) -> List[RecentItem]:
        result = await self.db.execute(
            select(SeoInsightResult)
            .where(SeoInsightResult.user_id == user_id)
            .order_by(SeoInsightResult.created_at.desc())
            .limit(limit)
        )
        insights = result.scalars().all()
        return [
            RecentItem(
                id=str(i.id),
                title=i.target_url,
                status=i.status.value if hasattr(i.status, 'value') else str(i.status),
                created_at=i.created_at,
                score=self._calculate_seo_score(i.base_url_checks)
            )
            for i in insights
        ]
    
    async def _get_recent_keyword_suggestions(self, user_id: str, limit: int = 3) -> List[RecentItem]:
        result = await self.db.execute(
            select(KeywordSuggestion)
            .where(KeywordSuggestion.user_id == user_id)
            .order_by(KeywordSuggestion.created_at.desc())
            .limit(limit)
        )
        suggestions = result.scalars().all()
        return [
            RecentItem(
                id=str(s.id),
                title=s.primary_keyword,
                status=s.status.value if hasattr(s.status, 'value') else str(s.status),
                created_at=s.created_at,
                score=len(s.related_searches) if s.related_searches else 0
            )
            for s in suggestions
        ]
    
    async def _get_recent_keyword_ranks(self, user_id: str, limit: int = 3) -> List[RecentItem]:
        result = await self.db.execute(
            select(KeywordRankResult)
            .where(KeywordRankResult.user_id == user_id)
            .order_by(KeywordRankResult.created_at.desc())
            .limit(limit)
        )
        ranks = result.scalars().all()
        return [
            RecentItem(
                id=str(r.id),
                title=f"{r.keyword} - {r.target_domain or 'N/A'}",
                status=r.status.value if hasattr(r.status, 'value') else str(r.status),
                created_at=r.created_at,
                score=float(r.target_position) if r.target_position else None
            )
            for r in ranks
        ]
    
    async def _get_performance_chart(self, user_id: str) -> List[PerformanceChartItem]:
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        return [
            PerformanceChartItem(label=day, value=float(idx * 10 + 50), color="#3b82f6")
            for idx, day in enumerate(days)
        ]