import asyncio
import sys
import os
from uuid import UUID
from datetime import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from sqlalchemy import select
from backend.app.database.models import AgentEvent
from backend.app.database.session import SessionLocal

async def get_events(agent_run_id_str: str):
    try:
        run_id = UUID(agent_run_id_str)
    except ValueError:
        print(f"Invalid UUID: {agent_run_id_str}")
        return

    async with SessionLocal() as db:
        query = (
            select(AgentEvent)
            .where(AgentEvent.agent_run_id == run_id)
            .order_by(AgentEvent.timestamp.asc())
        )
        result = await db.execute(query)
        events = result.scalars().all()

        if not events:
            print("No events found.")
            return

        for e in events:
            print(f"[{e.timestamp}] {e.event_type}: {e.message}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(get_events(sys.argv[1]))
    else:
        print("Usage: python inspect_agent_events.py <agent_run_id>")
