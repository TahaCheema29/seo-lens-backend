from typing import Generic, TypeVar, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Any, session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, obj: Any) -> Any:
        """Create a new record"""
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def get_by_id(self, id: Any) -> Optional[Any]:
        """Get a record by ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Any]:
        """Get all records with pagination"""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def update(self, id: Any, **kwargs) -> Optional[Any]:
        """Update a record by ID"""
        obj = await self.get_by_id(id)
        if obj:
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            await self.session.commit()
            await self.session.refresh(obj)
        return obj
    
    async def delete(self, id: Any) -> bool:
        """Delete a record by ID"""
        obj = await self.get_by_id(id)
        if obj:
            await self.session.delete(obj)
            await self.session.commit()
            return True
        return False
    
    async def count(self) -> int:
        """Count total records"""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()