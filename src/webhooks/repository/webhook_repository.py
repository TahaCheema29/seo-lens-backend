from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.cicd_integration import APIKey, WebhookConfig, WebhookEvent, DeploymentAnalysis
from src.auth.repository.base_repository import BaseRepository
import hashlib


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for API Key management"""

    def __init__(self, session: AsyncSession):
        super().__init__(APIKey, session)

    async def get_by_key_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by its hash"""
        result = await self.session.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[APIKey]:
        """Get all API keys for a user"""
        result = await self.session.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_active_by_user_id(self, user_id: UUID) -> List[APIKey]:
        """Get active API keys for a user"""
        result = await self.session.execute(
            select(APIKey)
            .where(and_(APIKey.user_id == user_id, APIKey.is_active == True))
        )
        return result.scalars().all()

    async def deactivate(self, key_id: UUID) -> Optional[APIKey]:
        """Deactivate an API key"""
        return await self.update(key_id, is_active=False)

    async def update_last_used(self, key_id: UUID) -> None:
        """Update the last used timestamp"""
        from datetime import datetime
        await self.update(key_id, last_used_at=datetime.utcnow())

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()


class WebhookConfigRepository(BaseRepository[WebhookConfig]):
    """Repository for Webhook Config management"""

    def __init__(self, session: AsyncSession):
        super().__init__(WebhookConfig, session)

    async def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[WebhookConfig]:
        """Get all webhook configs for a user"""
        result = await self.session.execute(
            select(WebhookConfig)
            .where(WebhookConfig.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_repository(self, user_id: UUID, provider: str, repository_name: str) -> Optional[WebhookConfig]:
        """Get webhook config by repository"""
        result = await self.session.execute(
            select(WebhookConfig)
            .where(
                and_(
                    WebhookConfig.user_id == user_id,
                    WebhookConfig.provider == provider,
                    WebhookConfig.repository_name == repository_name
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_configs(self, skip: int = 0, limit: int = 100) -> List[WebhookConfig]:
        """Get all active webhook configs"""
        result = await self.session.execute(
            select(WebhookConfig)
            .where(WebhookConfig.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class WebhookEventRepository(BaseRepository[WebhookEvent]):
    """Repository for Webhook Event logging"""

    def __init__(self, session: AsyncSession):
        super().__init__(WebhookEvent, session)

    async def get_by_config_id(self, config_id: UUID, skip: int = 0, limit: int = 100) -> List[WebhookEvent]:
        """Get events for a specific webhook config"""
        result = await self.session.execute(
            select(WebhookEvent)
            .where(WebhookEvent.config_id == config_id)
            .order_by(desc(WebhookEvent.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_delivery_id(self, delivery_id: str) -> Optional[WebhookEvent]:
        """Get event by GitHub/GitLab delivery ID"""
        result = await self.session.execute(
            select(WebhookEvent).where(WebhookEvent.delivery_id == delivery_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, event_id: UUID, status: str, error_message: str = None) -> Optional[WebhookEvent]:
        """Update event status"""
        updates = {"status": status}
        if error_message:
            updates["error_message"] = error_message
        return await self.update(event_id, **updates)


class DeploymentAnalysisRepository(BaseRepository[DeploymentAnalysis]):
    """Repository for Deployment Analysis tracking"""

    def __init__(self, session: AsyncSession):
        super().__init__(DeploymentAnalysis, session)

    async def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[DeploymentAnalysis]:
        """Get all deployment analyses for a user"""
        result = await self.session.execute(
            select(DeploymentAnalysis)
            .where(DeploymentAnalysis.user_id == user_id)
            .order_by(desc(DeploymentAnalysis.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_job_id(self, job_id: str) -> Optional[DeploymentAnalysis]:
        """Get analysis by job ID"""
        result = await self.session.execute(
            select(DeploymentAnalysis).where(DeploymentAnalysis.job_id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_by_repository(self, user_id: UUID, repository_name: str, skip: int = 0, limit: int = 100) -> List[DeploymentAnalysis]:
        """Get analyses for a specific repository"""
        result = await self.session.execute(
            select(DeploymentAnalysis)
            .where(
                and_(
                    DeploymentAnalysis.user_id == user_id,
                    DeploymentAnalysis.repository_name == repository_name
                )
            )
            .order_by(desc(DeploymentAnalysis.created_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_status(self, analysis_id: UUID, status: str, score: int = None, seo_insight_id: UUID = None) -> Optional[DeploymentAnalysis]:
        """Update analysis status"""
        from datetime import datetime
        updates = {"status": status}
        if score is not None:
            updates["score"] = score
        if seo_insight_id:
            updates["seo_insight_id"] = seo_insight_id
        if status in ["completed", "failed"]:
            updates["completed_at"] = datetime.utcnow()
        return await self.update(analysis_id, **updates)
