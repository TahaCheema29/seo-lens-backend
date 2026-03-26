from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import Admin
from src.auth.repository.base_repository import BaseRepository


class AdminRepository(BaseRepository[Admin]):
    """Repository for Admin model"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Admin, session)
    
    async def get_by_email(self, email: str) -> Optional[Admin]:
        """Get admin by email"""
        result = await self.session.execute(
            select(Admin).where(Admin.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_all_admins(self, skip: int = 0, limit: int = 100) -> List[Admin]:
        """Get all admins with pagination"""
        result = await self.session.execute(
            select(Admin).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_admins(self, skip: int = 0, limit: int = 100) -> List[Admin]:
        """Get all active admins"""
        result = await self.session.execute(
            select(Admin).where(Admin.is_active == True).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def activate(self, admin_id: str) -> Optional[Admin]:
        """Activate admin"""
        return await self.update(admin_id, is_active=True)
    
    async def deactivate(self, admin_id: str) -> Optional[Admin]:
        """Deactivate admin"""
        return await self.update(admin_id, is_active=False)
    
    async def set_super_admin(self, admin_id: str, is_super: bool = True) -> Optional[Admin]:
        """Set super admin status"""
        return await self.update(admin_id, is_super_admin=is_super)