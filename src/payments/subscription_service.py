"""
Subscription Service
Business logic for subscription management
"""
from typing import Optional
from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from src.config.settings import settings
from src.config.stripe_config import stripe_client
from src.payments.subscription_repository import SubscriptionRepository
from src.models.subscription import Subscription, SubscriptionTier, SubscriptionStatus

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = SubscriptionRepository(db)
    
    async def get_subscription(self, user_id: UUID | str) -> Subscription:
        """Get or create subscription for user"""
        subscription = await self.repository.get_by_user_id(user_id)
        
        if not subscription:
            # Auto-create Standard subscription if none exists
            logger.info(f"Creating Standard subscription for user {user_id}")
            subscription = await self.repository.create_standard_subscription(user_id)
        
        return subscription
    
    async def is_pro_user(self, user_id: UUID | str) -> bool:
        """Check if user has Pro subscription"""
        subscription = await self.get_subscription(user_id)
        return subscription.can_access_pro_features
    
    async def create_checkout_session(
        self,
        user_id: UUID | str,
        user_email: str,
    ) -> dict:
        """
        Create Stripe checkout session for Pro subscription
        
        Returns checkout session URL for user to complete payment
        """
        try:
            # Get or create Stripe customer
            subscription = await self.get_subscription(user_id)
            
            if subscription.stripe_customer_id:
                customer_id = subscription.stripe_customer_id
            else:
                # Create new Stripe customer
                customer = stripe_client.Customer.create(
                    email=user_email,
                    metadata={
                        "user_id": str(user_id),
                    }
                )
                customer_id = customer.id
                logger.info(f"Created Stripe customer {customer_id} for user {user_id}")
            
            # Create checkout session
            checkout_session = stripe_client.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[
                    {
                        "price": settings.stripe_price_id,
                        "quantity": 1,
                    }
                ],
                mode="payment",  # One-time payment
                success_url=f"{settings.frontend_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.frontend_url}/payment/cancel",
                metadata={
                    "user_id": str(user_id),
                    "tier": "pro",
                },
            )
            
            # Store checkout session ID
            await self.repository.update_checkout_session_id(
                user_id,
                checkout_session.id
            )
            
            logger.info(f"Created checkout session {checkout_session.id} for user {user_id}")
            
            return {
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id,
            }
            
        except stripe_client.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating checkout session: {e}")
            raise
    
    async def handle_checkout_completed(self, session: dict) -> Subscription:
        """
        Handle successful checkout session completion
        
        Called by webhook when payment is successful
        """
        user_id = session.get("metadata", {}).get("user_id")
        customer_id = session.get("customer")
        
        if not user_id:
            logger.error("No user_id in checkout session metadata")
            raise ValueError("No user_id in session metadata")
        
        logger.info(f"Processing checkout completion for user {user_id}")
        
        # For one-time payments, we create a subscription record
        # but stripe_subscription_id will be None since it's not a subscription
        subscription = await self.repository.upgrade_to_pro(
            user_id=user_id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=None,  # One-time payment, not a subscription
        )
        
        logger.info(f"User {user_id} upgraded to Pro")
        return subscription
    
    async def handle_payment_intent_succeeded(self, payment_intent: dict) -> None:
        """
        Handle successful payment intent
        
        Additional processing if needed
        """
        logger.info(f"Payment intent succeeded: {payment_intent.get('id')}")
        # Additional logic if needed (e.g., send confirmation email)
    
    async def handle_payment_intent_failed(self, payment_intent: dict) -> None:
        """Handle failed payment"""
        logger.warning(f"Payment intent failed: {payment_intent.get('id')}")
        # Log the failure, potentially notify user
    
    async def get_subscription_status(self, user_id: UUID | str) -> dict:
        """Get subscription status for response"""
        subscription = await self.get_subscription(user_id)
        
        return {
            "tier": subscription.tier.value,
            "status": subscription.status.value,
            "is_pro": subscription.is_pro,
            "can_access_pro_features": subscription.can_access_pro_features,
            "is_lifetime": subscription.is_lifetime,
        }
