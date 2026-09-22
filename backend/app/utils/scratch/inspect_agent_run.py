import asyncio
import sys
import os
from uuid import UUID

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from sqlalchemy import select
from backend.app.database.models import AgentRun
from backend.app.database.session import SessionLocal

async def get_run(agent_run_id_str: str):
    try:
        run_id = UUID(agent_run_id_str)
    except ValueError:
        print(f"Invalid UUID: {agent_run_id_str}")
        return

    async with SessionLocal() as db:
        query = select(AgentRun).where(AgentRun.id == run_id)
        result = await db.execute(query)
        run = result.scalar_one_or_none()

        if run:
            print(f"ID: {run.id}")
            print(f"Status: {run.status}")
            print(f"Started At: {run.started_at}")
            print(f"Error Info: {run.error_info}")
        else:
            print(f"No run found for {agent_run_id_str}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(get_run(sys.argv[1]))
