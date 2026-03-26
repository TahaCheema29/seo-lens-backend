from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.keyword_rank import KeywordRankResult


class KeywordRankRepository:
    """Repository for KeywordRankResult model"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.model = KeywordRankResult
    
    async def create(self, obj: KeywordRankResult) -> KeywordRankResult:
        """Create a new record"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def get_by_id(self, id: str) -> Optional[KeywordRankResult]:
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
    ) -> List[KeywordRankResult]:
        """Get all keyword rank results for a user"""
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
    ) -> Optional[KeywordRankResult]:
        """Get a specific keyword rank result by user and ID"""
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
        """Delete a record by ID"""
        obj = await self.get_by_id(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False