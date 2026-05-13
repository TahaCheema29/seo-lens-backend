import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.config.settings import settings
from src.billing.subscription_repository import SubscriptionRepository
from src.billing.billing_service import (
    process_checkout_session_completed,
    process_subscription_deleted,
    process_subscription_updated,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook is not configured",
        )

    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    if not sig:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Missing stripe-signature")

    import stripe

    try:
        event = await asyncio.to_thread(
            stripe.Webhook.construct_event,
            payload,
            sig,
            settings.stripe_webhook_secret,
        )
    except ValueError as e:
        logger.warning("Invalid webhook payload: %s", e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except Exception as e:
        err_name = type(e).__name__
        if "SignatureVerification" in err_name or "signature" in str(e).lower():
            logger.warning("Stripe signature verification failed: %s", e)
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid signature")
        logger.warning("Webhook construct_event failed: %s", e)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid webhook")

    event_id = getattr(event, "id", None) or event["id"]
    event_type = getattr(event, "type", None) or event["type"]
    data_object = event["data"]["object"]

    repo = SubscriptionRepository(db)
    if await repo.webhook_event_exists(event_id):
        return {"received": True}

    try:
        if event_type == "checkout.session.completed":
            await process_checkout_session_completed(db, data_object)
        elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
            await process_subscription_updated(db, data_object)
        elif event_type == "customer.subscription.deleted":
            await process_subscription_deleted(db, data_object)
        else:
            return {"received": True}

        repo.add_webhook_event(event_id)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        logger.info("Webhook idempotency conflict for event %s", event_id)
        return {"received": True}
    except Exception:
        await db.rollback()
        logger.exception("Webhook handler failed for %s", event_type)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )

    return {"received": True}
