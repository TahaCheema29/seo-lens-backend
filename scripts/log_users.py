"""
Log Users Script
Run this to display all users in the database
Usage: docker-compose exec backend python scripts/log_users.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from src.config.database import AsyncSessionLocal
from src.models.user import User

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

async def log_users():
    """Log all users from the database"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        
        logger.info("=" * 80)
        logger.info("USERS TABLE")
        logger.info("=" * 80)
        logger.info(f"{'ID':<36} | {'Email':<30} | {'Role':<10} | {'Active':<6} | {'Created At'}")
        logger.info("-" * 80)
        
        for user in users:
            logger.info(
                f"{str(user.id):<36} | {user.email:<30} | {user.role.value:<10} | "
                f"{str(user.is_active):<6} | {user.created_at}"
            )
        
        logger.info("-" * 80)
        logger.info(f"TOTAL USERS: {len(users)}")
        logger.info("=" * 80)

if __name__ == "__main__":
    asyncio.run(log_users())
