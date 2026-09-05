import asyncio
import sys
from sqlalchemy import text
from backend.app.database.session import engine
from backend.app.utils.logging import logger

async def verify_connection():
    try:
        logger.info("Attempting to connect to the database...")
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connectivity verified successfully.")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_connection())
    if not success:
        sys.exit(1)
