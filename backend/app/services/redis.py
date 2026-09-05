from redis.asyncio import Redis, from_url
from backend.app.config import settings
from backend.app.utils.logging import logger
from typing import Optional

class RedisService:
    def __init__(self):
        self._redis: Optional[Redis] = None

    async def connect(self):
        if not settings.REDIS_URL:
            logger.warning("REDIS_URL not configured. Redis service will be unavailable.")
            return

        try:
            self._redis = from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self._redis.ping()
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            self._redis = None

    async def disconnect(self):
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis.")

    @property
    def client(self) -> Optional[Redis]:
        return self._redis

redis_service = RedisService()

async def get_redis() -> Optional[Redis]:
    """Dependency for getting Redis client"""
    return redis_service.client
