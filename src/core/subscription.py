"""
Subscription Dependencies
Middleware and dependencies for protecting Pro-only routes
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.payments.subscription_service import SubscriptionService
from src.models.subscription import SubscriptionTier


class SubscriptionRequiredError(HTTPException):
    """Error raised when Pro subscription is required"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "status": False,
                "message": "This feature requires a Pro subscription",
                "data": {
                    "current_tier": "standard",
                    "required_tier": "pro",
                    "upgrade_url": "/api/payments/subscription/checkout"
                }
            }
        )


async def require_pro_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to require Pro subscription
    
    Usage:
        @router.get("/pro-feature", dependencies=[Depends(require_pro_subscription)])
        async def pro_feature():
            return {"message": "Pro feature"}
    """
    service = SubscriptionService(db)
    subscription = await service.get_subscription(current_user.id)
    
    if not subscription.can_access_pro_features:
        raise SubscriptionRequiredError()
    
    return current_user


async def get_subscription_tier(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    Get user's subscription tier
    
    Returns: "standard" or "pro"
    """
    service = SubscriptionService(db)
    subscription = await service.get_subscription(current_user.id)
    return subscription.tier.value


async def is_pro_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> bool:
    """
    Check if user has Pro subscription
    
    Returns: True if Pro, False otherwise
    """
    service = SubscriptionService(db)
    return await service.is_pro_user(current_user.id)


def check_pro_access(subscription_tier: str) -> bool:
    """
    Check if subscription tier has Pro access
    
    Args:
        subscription_tier: "standard" or "pro"
    
    Returns:
        True if Pro access, False otherwise
    """
    return subscription_tier == SubscriptionTier.PRO.value
