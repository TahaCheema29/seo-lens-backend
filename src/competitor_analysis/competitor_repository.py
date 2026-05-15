from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.competitor_analysis import CompetitorAnalysis, CompetitorAnalysisStatus


class CompetitorAnalysisRepository:
    """Repository for CompetitorAnalysis model"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = CompetitorAnalysis
    
    async def create(self, obj: CompetitorAnalysis) -> CompetitorAnalysis:
        """Create a new competitor analysis record"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def get_by_id(self, id: str) -> Optional[CompetitorAnalysis]:
        """Get a record by ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[CompetitorAnalysis]:
        """Get all competitor analyses for a user"""
        result = await self.session.execute(
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_user_and_id(
        self, 
        user_id: str, 
        analysis_id: str
    ) -> Optional[CompetitorAnalysis]:
        """Get a specific analysis by user and ID"""
        result = await self.session.execute(
            select(self.model).where(and_(
                self.model.user_id == user_id,
                self.model.id == analysis_id
            ))
        )
        return result.scalar_one_or_none()
    
    async def count_by_user(self, user_id: str) -> int:
        """Count total analyses for a user"""
        result = await self.session.execute(
            select(func.count(self.model.id))
            .where(self.model.user_id == user_id)
        )
        return result.scalar_one()
    
    async def update_status(
        self, 
        analysis_id: str, 
        status: CompetitorAnalysisStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update analysis status"""
        analysis = await self.get_by_id(analysis_id)
        if analysis:
            analysis.status = status
            if error_message:
                analysis.error_message = error_message
            await self.session.commit()
    
    async def update_results(
        self,
        analysis_id: str,
        user_seo_data: dict,
        competitor_seo_data: dict,
        user_score: int,
        competitor_score: int,
        winner: str,
        score_gap: int,
        comparison_report: dict,
        suggestions: list,
        quick_wins: list,
        strengths: list,
        weaknesses: list
    ) -> None:
        """Update analysis with results"""
        analysis = await self.get_by_id(analysis_id)
        if analysis:
            analysis.user_seo_data = user_seo_data
            analysis.competitor_seo_data = competitor_seo_data
            analysis.user_score = user_score
            analysis.competitor_score = competitor_score
            analysis.winner = winner
            analysis.score_gap = score_gap
            analysis.comparison_report = comparison_report
            analysis.suggestions = suggestions
            analysis.quick_wins = quick_wins
            analysis.strengths = strengths
            analysis.weaknesses = weaknesses
            analysis.status = CompetitorAnalysisStatus.COMPLETED
            from datetime import datetime, timezone
            analysis.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
    
    async def delete(self, id: str) -> bool:
        """Delete a record by ID"""
        obj = await self.get_by_id(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False
