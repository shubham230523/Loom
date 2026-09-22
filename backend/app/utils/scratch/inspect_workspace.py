import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from sqlalchemy import select
from backend.app.database import SessionLocal, Contribution
from uuid import UUID

async def get_workspace_info(contribution_id_str: str):
    contribution_id = UUID(contribution_id_str)
    async with SessionLocal() as db:
        query = select(Contribution).where(Contribution.id == contribution_id)
        result = await db.execute(query)
        contribution = result.scalar_one_or_none()

        if contribution:
            print(f"Workspace ID: {contribution.workspace_id}")
            print(f"Branch Name: {contribution.branch_name}")
        else:
            print(f"No contribution found for {contribution_id_str}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(get_workspace_info(sys.argv[1]))
