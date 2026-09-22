import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from sqlalchemy import select
from backend.app.database.models import AgentRun
from backend.app.database.session import SessionLocal

async def find_latest():
    async with SessionLocal() as db:
        query = select(AgentRun).order_by(AgentRun.created_at.desc()).limit(5)
        result = await db.execute(query)
        runs = result.scalars().all()

        for r in runs:
            print(f"ID: {r.id}, Type: {r.agent_type}, Status: {r.status}, Created: {r.created_at}")

if __name__ == "__main__":
    asyncio.run(find_latest())
