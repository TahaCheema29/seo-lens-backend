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
        """Get average SEO score from stored scores"""
        result = await self.db.execute(
            select(SeoInsightResult).where(
                SeoInsightResult.user_id == user_id,
                SeoInsightResult.score.isnot(None)
            ).limit(10)
        )
        insights = result.scalars().all()
        if not insights:
            return 0.0
        scores = [insight.score for insight in insights if insight.score is not None]
        return sum(scores) / len(scores) if scores else 0.0
    
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
    
    async def get_seo_analyses(self, user_id: str) -> dict:
        """Get user's SEO analyses"""
        from src.models.enums import AnalysisStatus
        
        result = await self.db.execute(
            select(SeoInsightResult)
            .where(SeoInsightResult.user_id == user_id)
            .order_by(SeoInsightResult.created_at.desc())
        )
        insights = result.scalars().all()
        
        analyses = []
        for i in insights:
            # Use stored score if available, otherwise calculate from checks
            score = i.score if i.score is not None else 0
            
            # Count FAIL/WARNING from base_url_checks (frontend uses FAIL not CRITICAL)
            failed_issues = sum(1 for check in (i.base_url_checks or {}).values() 
                                if isinstance(check, dict) and check.get('status') == 'FAIL')
            warnings = sum(1 for check in (i.base_url_checks or {}).values() 
                         if isinstance(check, dict) and check.get('status') == 'WARNING')
            
            # Also count from url_results (same as frontend)
            url_check_keys = [
                'title_length_check', 'title_keyword_presence', 'meta_description_length_check',
                'meta_description_keyword_presence', 'h1_check', 'image_alt_check',
                'canonical_check', 'noindex_check', 'open_graph_check', 'schema_validation',
                'html_size_check', 'response_time_check', 'js_minification_check',
                'css_minification_check', 'mobile_responsiveness'
            ]
            
            for url_result in (i.url_results or []):
                if isinstance(url_result, dict):
                    for key in url_check_keys:
                        check = url_result.get(key)
                        if isinstance(check, dict):
                            status = check.get('status', '')
                            if status == 'FAIL':
                                failed_issues += 1
                            elif status == 'WARNING':
                                warnings += 1
            
            # Format crawl_mode for frontend
            crawl_mode = i.crawl_mode
            if hasattr(crawl_mode, 'value'):
                crawl_mode = crawl_mode.value
            elif isinstance(crawl_mode, str):
                # Already a string, use as-is
                pass
            
            analyses.append({
                "id": str(i.id),
                "url": i.target_url,
                "score": score,
                "status": i.status.value if hasattr(i.status, 'value') else str(i.status),
                "critical_issues": failed_issues,
                "warnings": warnings,
                "crawl_mode": crawl_mode,
                "created_at": i.created_at.isoformat() if i.created_at else None
            })
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="SEO analyses retrieved successfully",
            data=analyses
        )
    
    async def get_seo_analyses_stats(self, user_id: str) -> dict:
        """Get SEO analyses stats"""
        from src.models.enums import AnalysisStatus
        
        total = await self._count_seo_insights(user_id)
        
        completed_result = await self.db.execute(
            select(func.count()).where(
                SeoInsightResult.user_id == user_id,
                SeoInsightResult.status == AnalysisStatus.COMPLETED
            )
        )
        completed = completed_result.scalar() or 0
        
        processing_result = await self.db.execute(
            select(func.count()).where(
                SeoInsightResult.user_id == user_id,
                SeoInsightResult.status == AnalysisStatus.PROCESSING
            )
        )
        processing = processing_result.scalar() or 0
        
        failed_result = await self.db.execute(
            select(func.count()).where(
                SeoInsightResult.user_id == user_id,
                SeoInsightResult.status == AnalysisStatus.FAILED
            )
        )
        failed = failed_result.scalar() or 0
        
        avg_score = await self._get_avg_seo_score(user_id)
        
        # Calculate failed issues and warnings (from both base_url_checks and url_results)
        # Frontend uses 'FAIL' not 'CRITICAL'
        result = await self.db.execute(
            select(SeoInsightResult).where(SeoInsightResult.user_id == user_id)
        )
        insights = result.scalars().all()
        total_failed = 0
        total_warnings = 0
        
        url_check_keys = [
            'title_length_check', 'title_keyword_presence', 'meta_description_length_check',
            'meta_description_keyword_presence', 'h1_check', 'image_alt_check',
            'canonical_check', 'noindex_check', 'open_graph_check', 'schema_validation',
            'html_size_check', 'response_time_check', 'js_minification_check',
            'css_minification_check', 'mobile_responsiveness'
        ]
        
        for i in insights:
            # Count from base_url_checks
            if i.base_url_checks:
                total_failed += sum(1 for check in i.base_url_checks.values() 
                                    if isinstance(check, dict) and check.get('status') == 'FAIL')
                total_warnings += sum(1 for check in i.base_url_checks.values() 
                                    if isinstance(check, dict) and check.get('status') == 'WARNING')
            
            # Count from url_results
            for url_result in (i.url_results or []):
                if isinstance(url_result, dict):
                    for key in url_check_keys:
                        check = url_result.get(key)
                        if isinstance(check, dict):
                            status = check.get('status', '')
                            if status == 'FAIL':
                                total_failed += 1
                            elif status == 'WARNING':
                                total_warnings += 1
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="SEO analyses stats retrieved successfully",
            data={
                "total_count": total,
                "completed_count": completed,
                "processing_count": processing,
                "failed_count": failed,
                "avg_score": round(avg_score, 1),
                "total_critical_issues": total_failed,
                "total_warnings": total_warnings
            }
        )
    
    async def get_keywords(self, user_id: str) -> dict:
        """Get user's keyword suggestions"""
        result = await self.db.execute(
            select(KeywordSuggestion)
            .where(KeywordSuggestion.user_id == user_id)
            .order_by(KeywordSuggestion.created_at.desc())
        )
        suggestions = result.scalars().all()
        
        keywords = []
        for s in suggestions:
            keywords.append({
                "id": str(s.id),
                "primary_keyword": s.primary_keyword,
                "status": s.status.value if hasattr(s.status, 'value') else str(s.status),
                "related_keywords_count": len(s.related_searches) if s.related_searches else 0,
                "long_tail_keywords_count": len(s.long_tail_keywords) if s.long_tail_keywords else 0,
                "search_results_count": len(s.search_results) if s.search_results else 0,
                "created_at": s.created_at.isoformat() if s.created_at else None
            })
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Keyword suggestions retrieved successfully",
            data=keywords
        )
    
    async def get_keywords_stats(self, user_id: str) -> dict:
        """Get keyword stats"""
        from src.models.enums import AnalysisStatus
        
        total = await self._count_keyword_suggestions(user_id)
        
        completed_result = await self.db.execute(
            select(func.count()).where(
                KeywordSuggestion.user_id == user_id,
                KeywordSuggestion.status == AnalysisStatus.COMPLETED
            )
        )
        completed = completed_result.scalar() or 0
        
        processing_result = await self.db.execute(
            select(func.count()).where(
                KeywordSuggestion.user_id == user_id,
                KeywordSuggestion.status == AnalysisStatus.PROCESSING
            )
        )
        processing = processing_result.scalar() or 0
        
        failed_result = await self.db.execute(
            select(func.count()).where(
                KeywordSuggestion.user_id == user_id,
                KeywordSuggestion.status == AnalysisStatus.FAILED
            )
        )
        failed = failed_result.scalar() or 0
        
        # Calculate average related keywords
        result = await self.db.execute(
            select(KeywordSuggestion).where(
                KeywordSuggestion.user_id == user_id,
                KeywordSuggestion.status == AnalysisStatus.COMPLETED
            )
        )
        suggestions = result.scalars().all()
        avg_related = 0
        if suggestions:
            total_related = sum(len(s.related_searches) if s.related_searches else 0 for s in suggestions)
            avg_related = round(total_related / len(suggestions), 1)
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Keyword stats retrieved successfully",
            data={
                "total_count": total,
                "completed_count": completed,
                "processing_count": processing,
                "failed_count": failed,
                "avg_related_keywords": avg_related
            }
        )
    
    async def get_ranks(self, user_id: str) -> dict:
        """Get user's rank checks"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[SECURITY] Getting ranks for user_id: {user_id}")
        
        result = await self.db.execute(
            select(KeywordRankResult)
            .where(KeywordRankResult.user_id == user_id)
            .order_by(KeywordRankResult.created_at.desc())
        )
        ranks = result.scalars().all()
        
        # Debug: Log what we found
        logger.info(f"[SECURITY] Found {len(ranks)} rank checks for user {user_id}")
        for r in ranks[:3]:  # Log first 3
            logger.info(f"[SECURITY] - Rank {r.id}: user_id={r.user_id}, keyword={r.keyword}")
        
        rank_checks = []
        for r in ranks:
            rank_checks.append({
                "id": str(r.id),
                "domain": r.target_url,
                "keywords": r.keywords if r.keywords else [],
                "top10_count": sum(1 for sr in (r.search_results or []) if sr.get('position', 0) <= 10),
                "not_ranking_count": 0 if r.target_position else len(r.keywords or []),
                "avg_position": float(r.target_position) if r.target_position else None,
                "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
                "created_at": r.created_at.isoformat() if r.created_at else None
            })
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Rank checks retrieved successfully",
            data=rank_checks
        )
    
    async def get_ranks_stats(self, user_id: str) -> dict:
        """Get rank stats"""
        from src.models.enums import AnalysisStatus
        
        total = await self._count_keyword_ranks(user_id)
        
        completed_result = await self.db.execute(
            select(func.count()).where(
                KeywordRankResult.user_id == user_id,
                KeywordRankResult.status == AnalysisStatus.COMPLETED
            )
        )
        completed = completed_result.scalar() or 0
        
        processing_result = await self.db.execute(
            select(func.count()).where(
                KeywordRankResult.user_id == user_id,
                KeywordRankResult.status == AnalysisStatus.PROCESSING
            )
        )
        processing = processing_result.scalar() or 0
        
        failed_result = await self.db.execute(
            select(func.count()).where(
                KeywordRankResult.user_id == user_id,
                KeywordRankResult.status == AnalysisStatus.FAILED
            )
        )
        failed = failed_result.scalar() or 0
        
        # Count total keywords and top 10
        result = await self.db.execute(
            select(KeywordRankResult).where(KeywordRankResult.user_id == user_id)
        )
        ranks = result.scalars().all()
        total_keywords = sum(len(r.keywords) if r.keywords else 0 for r in ranks)
        total_top10 = sum(1 for r in ranks if r.target_position and r.target_position <= 10)
        
        return create_response(
            status=RESPONSE_STATUS_SUCCESS,
            message="Rank stats retrieved successfully",
            data={
                "total_count": total,
                "completed_count": completed,
                "processing_count": processing,
                "failed_count": failed,
                "total_keywords": total_keywords,
                "total_top10": total_top10
            }
        )