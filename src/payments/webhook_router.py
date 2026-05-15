"""
Stripe Webhook Router
Handles Stripe webhook events for subscription lifecycle
"""
import logging
from fastapi import APIRouter, Request, HTTPException, Header, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.stripe_config import stripe_client
from src.config.settings import settings
from src.config.database import get_db
from src.payments.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Webhooks"])


@router.post("/api/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """
    Handle Stripe webhook events
    
    This endpoint receives webhook events from Stripe:
    - checkout.session.completed: Payment successful, upgrade to Pro
    - payment_intent.payment_failed: Payment failed
    - charge.refunded: Refund processed
    
    The webhook must be configured in Stripe Dashboard with the webhook secret.
    """
    payload = await request.body()
    
    # Verify webhook signature
    if not stripe_signature:
        logger.error("Missing Stripe signature header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    try:
        # Verify and construct event
        event = stripe_client.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload"
        )
    except stripe_client.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"Invalid webhook signature: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    # Get database session
    db_gen = get_db()
    db = await db_gen.asend(None)
    
    try:
        service = SubscriptionService(db)
        event_type = event["type"]
        event_data = event["data"]["object"]
        
        logger.info(f"Processing Stripe webhook: {event_type}")
        
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(service, event_data)
            
        elif event_type == "payment_intent.payment_failed":
            await handle_payment_failed(event_data)
            
        elif event_type == "charge.refunded":
            await handle_refund(service, event_data)
            
        elif event_type == "payment_intent.succeeded":
            # Additional processing if needed
            logger.info(f"Payment intent succeeded: {event_data.get('id')}")
            
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        return JSONResponse(
            content={"received": True},
            status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        # Still return 200 to prevent Stripe from retrying
        # Log the error for manual review
        return JSONResponse(
            content={"received": True, "error": str(e)},
            status_code=status.HTTP_200_OK
        )
    finally:
        await db.close()


async def handle_checkout_completed(service: SubscriptionService, session: dict):
    """Handle successful checkout completion"""
    try:
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        tier = metadata.get("tier")
        
        if not user_id:
            logger.error("No user_id in checkout session metadata")
            return
        
        if tier == "pro":
            await service.handle_checkout_completed(session)
            logger.info(f"User {user_id} upgraded to Pro via checkout")
        
    except Exception as e:
        logger.error(f"Error handling checkout completion: {e}")
        raise


async def handle_payment_failed(payment_intent: dict):
    """Handle failed payment"""
    logger.warning(f"Payment failed for intent: {payment_intent.get('id')}")
    # Could send email notification to user
    # Could log for analytics


async def handle_refund(service: SubscriptionService, charge: dict):
    """Handle refund - downgrade user"""
    logger.info(f"Refund processed for charge: {charge.get('id')}")
    # For lifetime access, refunds are complex
    # You may want to implement a policy here
    # For now, just log it
