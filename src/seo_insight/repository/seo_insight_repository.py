from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.seo_insight import SeoInsightResult


class SeoInsightRepository:
    """Repository for SeoInsightResult model"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = SeoInsightResult
    
    async def create(self, obj: SeoInsightResult) -> SeoInsightResult:
        """Create a new record"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def get_by_id(self, id: str) -> Optional[SeoInsightResult]:
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
    ) -> List[SeoInsightResult]:
        """Get all SEO insight results for a user"""
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
        result_id: str
    ) -> Optional[SeoInsightResult]:
        """Get a specific SEO insight result by user and ID"""
        result = await self.session.execute(
            select(self.model).where(and_(
                self.model.user_id == user_id,
                self.model.id == result_id
            ))
        )
        return result.scalar_one_or_none()
    
    async def count_by_user(self, user_id: str) -> int:
        """Count total results for a user"""
        result = await self.session.execute(
            select(func.count(self.model.id))
            .where(self.model.user_id == user_id)
        )
        return result.scalar_one()
    
    async def delete(self, id: str) -> bool:
        """Delete a record by ID (WARNING: Does not check user ownership - use delete_by_user_and_id instead)"""
        obj = await self.get_by_id(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False

    async def delete_by_user_and_id(self, user_id: str, id: str) -> bool:
        """Delete a record by user_id and ID (SECURE - checks ownership)"""
        obj = await self.get_by_user_and_id(user_id, id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False