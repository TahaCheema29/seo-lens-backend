import redis.asyncio as redis
from src.config.settings import settings
import logging
import asyncio
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Parse the URL to extract components for explicit connection
parsed = urlparse(settings.redis_url)

# Create client with explicit parameters for better DNS resolution and error handling
redis_client = redis.Redis(
    host=parsed.hostname or 'redis',
    port=parsed.port or 6379,
    password=parsed.password or None,
    db=int(parsed.path.lstrip('/')) if parsed.path and parsed.path != '/' else 0,
    decode_responses=True,
    socket_connect_timeout=10,
    socket_timeout=10,
    retry_on_timeout=True,
    health_check_interval=30
)


async def ensure_redis_connection():
    """Ensure Redis connection is established with retry logic"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            await redis_client.ping()
            logger.info("Redis connection verified successfully")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Redis connection attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to Redis after {max_retries} attempts: {e}")
                return False
    return False