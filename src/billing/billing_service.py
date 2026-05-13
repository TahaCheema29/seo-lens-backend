from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.models.user import User
from src.models.subscription import PlanCode, SubscriptionStatus, UserSubscription
from src.billing.subscription_repository import SubscriptionRepository

logger = logging.getLogger(__name__)


def _configure_stripe() -> None:
    if settings.stripe_secret_key:
        stripe.api_key = settings.stripe_secret_key


def _stripe_val(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    v = getattr(obj, key, None)
    if v is not None:
        return v
    try:
        return obj[key]
    except Exception:
        return default


def _price_id_from_subscription(stripe_sub: Any) -> Optional[str]:
    try:
        items = _stripe_val(stripe_sub, "items")
        data = getattr(items, "data", None) or _stripe_val(items, "data", []) or []
        if not data:
            return None
        first = data[0]
        price = _stripe_val(first, "price")
        return _stripe_val(price, "id")
    except (KeyError, IndexError, AttributeError, TypeError):
        return None


def _map_stripe_status(status: str) -> SubscriptionStatus:
    mapping = {
        "active": SubscriptionStatus.ACTIVE,
        "trialing": SubscriptionStatus.TRIALING,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "unpaid": SubscriptionStatus.UNPAID,
        "incomplete": SubscriptionStatus.INCOMPLETE,
        "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
        "paused": SubscriptionStatus.PAUSED,
    }
    return mapping.get(status, SubscriptionStatus.ACTIVE)


async def create_pro_checkout_session(
    user: User,
    success_path: str = "/billing/success",
    cancel_path: str = "/billing/cancel",
) -> dict[str, Any]:
    _configure_stripe()
    if not settings.stripe_secret_key or not settings.stripe_pro_price_id:
        raise ValueError("Stripe is not configured (STRIPE_SECRET_KEY / STRIPE_PRO_PRICE_ID).")

    base = settings.frontend_base_url.rstrip("/")
    success_url = f"{base}{success_path}?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base}{cancel_path}?session_id={{CHECKOUT_SESSION_ID}}"

    params: dict[str, Any] = {
        "mode": "subscription",
        "line_items": [{"price": settings.stripe_pro_price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": str(user.id),
        "metadata": {"user_id": str(user.id)},
        "subscription_data": {"metadata": {"user_id": str(user.id)}},
    }
    if user.stripe_customer_id:
        params["customer"] = user.stripe_customer_id
    else:
        params["customer_email"] = user.email

    session = await asyncio.to_thread(stripe.checkout.Session.create, **params)
    return {"id": session.id, "url": session.url}


async def retrieve_checkout_session(session_id: str) -> Any:
    _configure_stripe()
    return await asyncio.to_thread(stripe.checkout.Session.retrieve, session_id)


async def retrieve_subscription(subscription_id: str) -> Any:
    _configure_stripe()
    return await asyncio.to_thread(stripe.Subscription.retrieve, subscription_id)


async def process_checkout_session_completed(
    db: AsyncSession, session: Any
) -> None:
    if _stripe_val(session, "mode") != "subscription":
        return
    meta = _stripe_val(session, "metadata") or {}
    user_id_str = None
    if isinstance(meta, dict):
        user_id_str = meta.get("user_id")
    else:
        user_id_str = getattr(meta, "user_id", None)
    user_id_str = user_id_str or _stripe_val(session, "client_reference_id")
    if not user_id_str:
        logger.warning("checkout.session.completed missing user_id metadata")
        return
    try:
        user_id = UUID(str(user_id_str))
    except ValueError:
        logger.warning("Invalid user_id in checkout session: %s", user_id_str)
        return

    sub_id = _stripe_val(session, "subscription")
    customer_id = _stripe_val(session, "customer")
    if not sub_id:
        logger.warning("checkout.session.completed missing subscription id")
        return

    stripe_sub = await retrieve_subscription(sub_id)
    await _apply_stripe_subscription_to_user(db, user_id, customer_id, stripe_sub)


async def process_subscription_updated(db: AsyncSession, stripe_sub: Any) -> None:
    repo = SubscriptionRepository(db)
    stripe_sub_id = _stripe_val(stripe_sub, "id")
    customer_id = _stripe_val(stripe_sub, "customer")
    row = await repo.get_by_stripe_subscription_id(stripe_sub_id)
    if not row:
        meta = _stripe_val(stripe_sub, "metadata") or {}
        user_id_str = None
        if isinstance(meta, dict):
            user_id_str = meta.get("user_id")
        else:
            user_id_str = getattr(meta, "user_id", None)
        if user_id_str:
            try:
                uid = UUID(str(user_id_str))
            except ValueError:
                logger.info("subscription event with invalid user_id metadata")
                return
            await _apply_stripe_subscription_to_user(db, uid, customer_id, stripe_sub)
        else:
            logger.info(
                "subscription.updated for unknown subscription %s (no user metadata)",
                stripe_sub_id,
            )
        return
    await _apply_stripe_subscription_to_user(db, row.user_id, customer_id, stripe_sub)


async def process_subscription_deleted(db: AsyncSession, stripe_sub: Any) -> None:
    stripe_sub_id = _stripe_val(stripe_sub, "id")
    repo = SubscriptionRepository(db)
    row = await repo.get_by_stripe_subscription_id(stripe_sub_id)
    if not row:
        return
    row.plan_code = PlanCode.BASIC
    row.stripe_subscription_id = None
    row.stripe_price_id = None
    row.status = SubscriptionStatus.ACTIVE
    row.current_period_start = None
    row.current_period_end = None
    row.cancel_at_period_end = False


async def _apply_stripe_subscription_to_user(
    db: AsyncSession,
    user_id: UUID,
    customer_id: Optional[str],
    stripe_sub: Any,
) -> None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        logger.warning("User %s not found for Stripe subscription sync", user_id)
        return

    if customer_id and user.stripe_customer_id != customer_id:
        user.stripe_customer_id = customer_id

    price_id = _price_id_from_subscription(stripe_sub)
    sid = _stripe_val(stripe_sub, "id")
    st = _stripe_val(stripe_sub, "status", "active")
    cps = _stripe_val(stripe_sub, "current_period_start")
    cpe = _stripe_val(stripe_sub, "current_period_end")
    care = _stripe_val(stripe_sub, "cancel_at_period_end", False)

    repo = SubscriptionRepository(db)
    sub_row = await repo.get_by_user_id(user_id)
    if not sub_row:
        sub_row = UserSubscription(
            user_id=user_id,
            plan_code=PlanCode.PRO,
            status=_map_stripe_status(str(st)),
            stripe_subscription_id=sid,
            stripe_price_id=price_id,
            current_period_start=_ts_to_dt(cps),
            current_period_end=_ts_to_dt(cpe),
            cancel_at_period_end=bool(care),
        )
        db.add(sub_row)
    else:
        sub_row.plan_code = PlanCode.PRO
        sub_row.stripe_subscription_id = sid
        sub_row.stripe_price_id = price_id
        sub_row.status = _map_stripe_status(str(st))
        sub_row.current_period_start = _ts_to_dt(cps)
        sub_row.current_period_end = _ts_to_dt(cpe)
        sub_row.cancel_at_period_end = bool(care)


def _ts_to_dt(ts: Any):
    if ts is None:
        return None
    from datetime import datetime, timezone

    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).replace(tzinfo=None)
    except (TypeError, ValueError, OSError):
        return None
