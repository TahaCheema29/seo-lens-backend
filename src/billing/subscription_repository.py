from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import (
    PlanCode,
    StripeWebhookEvent,
    SubscriptionStatus,
    UserSubscription,
)


class SubscriptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserSubscription]:
        result = await self.session.execute(
            select(UserSubscription).where(UserSubscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_stripe_subscription_id(
        self, stripe_subscription_id: str
    ) -> Optional[UserSubscription]:
        result = await self.session.execute(
            select(UserSubscription).where(
                UserSubscription.stripe_subscription_id == stripe_subscription_id
            )
        )
        return result.scalar_one_or_none()

    async def create_basic(self, user_id: uuid.UUID) -> UserSubscription:
        sub = UserSubscription(
            user_id=user_id,
            plan_code=PlanCode.BASIC,
            status=SubscriptionStatus.ACTIVE,
            cancel_at_period_end=False,
        )
        self.session.add(sub)
        await self.session.commit()
        await self.session.refresh(sub)
        return sub

    async def ensure_basic(self, user_id: uuid.UUID) -> UserSubscription:
        existing = await self.get_by_user_id(user_id)
        if existing:
            return existing
        return await self.create_basic(user_id)

    async def webhook_event_exists(self, stripe_event_id: str) -> bool:
        result = await self.session.execute(
            select(StripeWebhookEvent.id).where(
                StripeWebhookEvent.stripe_event_id == stripe_event_id
            )
        )
        return result.scalar_one_or_none() is not None

    def add_webhook_event(self, stripe_event_id: str) -> None:
        self.session.add(StripeWebhookEvent(stripe_event_id=stripe_event_id))
