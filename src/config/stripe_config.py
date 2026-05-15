"""
Stripe configuration module
"""
import stripe
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe with secret key
stripe_secret = settings.stripe_secret_key
if not stripe_secret:
    logger.error("[STRIPE] STRIPE_SECRET_KEY is not set! Check your .env.docker file")
    raise ValueError("STRIPE_SECRET_KEY is required but not set in environment")

stripe.api_key = stripe_secret
logger.info(f"[STRIPE] Initialized with key starting with: {stripe_secret[:8]}...")

# Export stripe module for use across the application
stripe_client = stripe
