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


@router.get("/api/webhooks/stripe/test")
async def test_webhook_endpoint():
    """Test endpoint to verify webhook route is accessible"""
    logger.info("[WEBHOOK TEST] Webhook test endpoint called")
    return {"status": "ok", "message": "Webhook endpoint is accessible"}


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
    logger.info("=" * 80)
    logger.info("[WEBHOOK] Received webhook request")
    logger.info(f"[WEBHOOK] URL: {request.url}")
    logger.info(f"[WEBHOOK] Method: {request.method}")
    
    # Get all headers
    headers_dict = dict(request.headers)
    logger.info(f"[WEBHOOK] All headers: {headers_dict}")
    
    payload = await request.body()
    logger.info(f"[WEBHOOK] Payload size: {len(payload)} bytes")
    logger.info(f"[WEBHOOK] Payload preview: {payload[:200]}...")
    
    # Check for stripe-signature header (case insensitive)
    stripe_sig_header = None
    for key, value in headers_dict.items():
        if key.lower() == "stripe-signature":
            stripe_sig_header = value
            logger.info(f"[WEBHOOK] Found stripe-signature header (key: {key}): {value[:30]}...")
            break
    
    if not stripe_sig_header and not stripe_signature:
        logger.error("[WEBHOOK] Missing Stripe signature header")
        logger.error(f"[WEBHOOK] Available headers: {list(headers_dict.keys())}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    # Use whichever signature we found
    sig_to_use = stripe_signature or stripe_sig_header
    logger.info(f"[WEBHOOK] Using signature: {sig_to_use[:30]}...")
    
    try:
        # Verify and construct event
        logger.info("[WEBHOOK] Verifying webhook signature...")
        event = stripe_client.Webhook.construct_event(
            payload,
            sig_to_use,
            settings.stripe_webhook_secret
        )
        logger.info("[WEBHOOK] Signature verified successfully")
    except ValueError as e:
        # Invalid payload
        logger.error(f"[WEBHOOK] Invalid webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload"
        )
    except stripe_client.error.SignatureVerificationError as e:
        # Invalid signature - reject the webhook
        logger.error(f"[WEBHOOK] Invalid webhook signature: {e}")
        logger.error(f"[WEBHOOK] Signature used: {sig_to_use[:50]}...")
        logger.error(f"[WEBHOOK] Secret configured: {settings.stripe_webhook_secret[:20]}... (length: {len(settings.stripe_webhook_secret)})")
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
        logger.info(f"[WEBHOOK] Processing checkout.session.completed")
        logger.info(f"[WEBHOOK] Session ID: {session.get('id')}")
        logger.info(f"[WEBHOOK] Session data: {session}")
        
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        tier = metadata.get("tier")
        
        logger.info(f"[WEBHOOK] Metadata: user_id={user_id}, tier={tier}")
        
        if not user_id:
            logger.error("[WEBHOOK] No user_id in checkout session metadata")
            return
        
        if tier == "pro":
            logger.info(f"[WEBHOOK] Upgrading user {user_id} to Pro...")
            result = await service.handle_checkout_completed(session)
            logger.info(f"[WEBHOOK] User {user_id} upgraded to Pro successfully: {result}")
        else:
            logger.warning(f"[WEBHOOK] Unknown tier '{tier}', skipping upgrade")
        
    except Exception as e:
        logger.error(f"[WEBHOOK] Error handling checkout completion: {e}")
        logger.exception(e)
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
