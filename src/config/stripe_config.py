"""
Stripe configuration module
"""
import stripe
from src.config.settings import settings

# Initialize Stripe with secret key
stripe.api_key = settings.stripe_secret_key

# Export stripe module for use across the application
stripe_client = stripe
