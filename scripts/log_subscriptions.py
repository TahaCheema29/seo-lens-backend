"""
Log Subscriptions Script
Run this to display all subscriptions in the database
Usage: docker-compose exec backend python scripts/log_subscriptions.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from src.config.database import AsyncSessionLocal
from src.models.subscription import Subscription
from src.models.user import User

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def log_subscriptions():
    """Log all subscriptions from the database with user info"""
    async with AsyncSessionLocal() as session:
        # Get subscriptions with user info
        result = await session.execute(
            select(Subscription, User)
            .join(User, Subscription.user_id == User.id)
            .order_by(Subscription.created_at.desc())
        )
        subscriptions = result.all()
        
        logger.info("=" * 120)
        logger.info("SUBSCRIPTIONS TABLE")
        logger.info("=" * 120)
        logger.info(
            f"{'User Email':<30} | {'Tier':<10} | {'Status':<10} | "
            f"{'Is Lifetime':<12} | {'Stripe Customer':<20} | {'Created At'}"
        )
        logger.info("-" * 120)
        
        for subscription, user in subscriptions:
            stripe_customer = subscription.stripe_customer_id or "N/A"
            if stripe_customer != "N/A":
                stripe_customer = stripe_customer[:15] + "..."
            
            logger.info(
                f"{user.email:<30} | {subscription.tier.value:<10} | "
                f"{subscription.status.value:<10} | {str(subscription.is_lifetime):<12} | "
                f"{stripe_customer:<20} | {subscription.created_at}"
            )
        
        logger.info("-" * 120)
        logger.info(f"TOTAL SUBSCRIPTIONS: {len(subscriptions)}")
        
        # Summary by tier
        if subscriptions:
            standard_count = sum(1 for s, _ in subscriptions if s.tier.value == "standard")
            pro_count = sum(1 for s, _ in subscriptions if s.tier.value == "pro")
            logger.info(f"Standard: {standard_count}, Pro: {pro_count}")
        
        logger.info("=" * 120)

if __name__ == "__main__":
    asyncio.run(log_subscriptions())
