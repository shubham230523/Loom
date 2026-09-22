import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from sqlalchemy import select
from backend.app.database.models import TestRun
from backend.app.database.session import SessionLocal

async def get_test_runs():
    async with SessionLocal() as db:
        query = select(TestRun).order_by(TestRun.timestamp.desc()).limit(5)
        result = await db.execute(query)
        runs = result.scalars().all()

        for r in runs:
            print(f"ID: {r.id}, Status: {r.status}, Exit Code: {r.exit_code}, Time: {r.timestamp}")

if __name__ == "__main__":
    asyncio.run(get_test_runs())
