"""
Subscription Repository
Database operations for subscriptions
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.subscription import Subscription, SubscriptionTier, SubscriptionStatus


class SubscriptionRepository:
    """Repository for subscription database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_user_id(self, user_id: UUID | str) -> Optional[Subscription]:
        """Get subscription by user ID"""
        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe customer ID"""
        result = await self.db.execute(
            select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_stripe_subscription_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID"""
        result = await self.db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
        )
        return result.scalar_one_or_none()
    
    async def create_standard_subscription(self, user_id: UUID | str) -> Subscription:
        """Create a new Standard (free) subscription for a user"""
        subscription = Subscription(
            user_id=user_id,
            tier=SubscriptionTier.STANDARD,
            status=SubscriptionStatus.ACTIVE,
            is_lifetime=False,
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription
    
    async def upgrade_to_pro(
        self,
        user_id: UUID | str,
        stripe_customer_id: str,
        stripe_subscription_id: str,
    ) -> Subscription:
        """Upgrade user to Pro tier"""
        subscription = await self.get_by_user_id(user_id)
        
        if not subscription:
            # Create new Pro subscription
            subscription = Subscription(
                user_id=user_id,
                stripe_customer_id=stripe_customer_id,
                stripe_subscription_id=stripe_subscription_id,
                tier=SubscriptionTier.PRO,
                status=SubscriptionStatus.ACTIVE,
                is_lifetime=True,  # One-time payment, lifetime access
            )
            self.db.add(subscription)
        else:
            # Update existing subscription
            subscription.stripe_customer_id = stripe_customer_id
            subscription.stripe_subscription_id = stripe_subscription_id
            subscription.tier = SubscriptionTier.PRO
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.is_lifetime = True
        
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription
    
    async def update_status(
        self,
        user_id: UUID | str,
        status: SubscriptionStatus,
    ) -> Optional[Subscription]:
        """Update subscription status"""
        subscription = await self.get_by_user_id(user_id)
        if subscription:
            subscription.status = status
            await self.db.commit()
            await self.db.refresh(subscription)
        return subscription
    
    async def update_checkout_session_id(
        self,
        user_id: UUID | str,
        checkout_session_id: str,
    ) -> Optional[Subscription]:
        """Update Stripe checkout session ID"""
        subscription = await self.get_by_user_id(user_id)
        if subscription:
            subscription.stripe_checkout_session_id = checkout_session_id
            await self.db.commit()
            await self.db.refresh(subscription)
        return subscription
    
    async def delete_subscription(self, user_id: UUID | str) -> bool:
        """Delete subscription (downgrade to nothing)"""
        subscription = await self.get_by_user_id(user_id)
        if subscription:
            await self.db.delete(subscription)
            await self.db.commit()
            return True
        return False
