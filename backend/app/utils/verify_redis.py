import asyncio
import sys
from backend.app.services.redis import redis_service
from backend.app.utils.logging import logger

async def verify_connection():
    try:
        logger.info("Attempting to connect to Redis...")
        await redis_service.connect()
        if redis_service.client:
            await redis_service.client.set("loom_test", "ok", ex=10)
            val = await redis_service.client.get("loom_test")
            if val == "ok":
                logger.info("Redis connectivity verified successfully.")
                await redis_service.disconnect()
                return True
        logger.error("Redis client not initialized.")
        return False
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_connection())
    if not success:
        sys.exit(1)
