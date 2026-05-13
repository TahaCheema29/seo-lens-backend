from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.subscription import PlanCode, SubscriptionStatus
from src.billing.subscription_repository import SubscriptionRepository


PRO_REQUIRED_MESSAGE = (
    "This feature requires an active Pro subscription. "
    "Upgrade to Pro to use competitor analysis, full-site (auto) analysis, and related tools."
)

_PRO_STATUSES = frozenset(
    {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.TRIALING,
        SubscriptionStatus.PAST_DUE,
    }
)


def subscription_has_pro_access(sub) -> bool:
    if sub is None or sub.plan_code != PlanCode.PRO:
        return False
    return sub.status in _PRO_STATUSES


async def user_has_pro_access(db: AsyncSession, user_id: uuid.UUID) -> bool:
    repo = SubscriptionRepository(db)
    sub = await repo.get_by_user_id(user_id)
    return subscription_has_pro_access(sub)


async def assert_active_pro(db: AsyncSession, user_id: uuid.UUID) -> None:
    repo = SubscriptionRepository(db)
    sub = await repo.get_by_user_id(user_id)
    if sub is None:
        sub = await repo.ensure_basic(user_id)
    if not subscription_has_pro_access(sub):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "PRO_REQUIRED", "message": PRO_REQUIRED_MESSAGE},
        )


async def assert_active_pro_optional_user(
    db: AsyncSession, user_id: Optional[uuid.UUID]
) -> None:
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this analysis mode.",
        )
    await assert_active_pro(db, user_id)
