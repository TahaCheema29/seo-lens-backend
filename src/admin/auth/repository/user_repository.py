from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User, UserRole
from src.auth.repository.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update_role(self, user_id: str, role: UserRole) -> Optional[User]:
        """Update user role"""
        return await self.update(user_id, role=role)
    
    async def activate(self, user_id: str) -> Optional[User]:
        """Activate user"""
        return await self.update(user_id, is_active=True)
    
    async def deactivate(self, user_id: str) -> Optional[User]:
        """Deactivate user"""
        return await self.update(user_id, is_active=False)