import redis.asyncio as redis
from src.config.settings import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)