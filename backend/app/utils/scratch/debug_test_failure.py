import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from sqlalchemy import select
from backend.app.database import SessionLocal, TestRun, Contribution
from uuid import UUID

async def get_latest_failure(contribution_id_str: str):
    contribution_id = UUID(contribution_id_str)
    async with SessionLocal() as db:
        query = (
            select(TestRun)
            .where(TestRun.contribution_id == contribution_id)
            .order_by(TestRun.timestamp.desc())
            .limit(1)
        )
        result = await db.execute(query)
        test_run = result.scalar_one_or_none()

        if test_run:
            print(f"Test Run ID: {test_run.id}")
            print(f"Status: {test_run.status}")
            print(f"Exit Code: {test_run.exit_code}")
            print(f"Command: {test_run.command}")
            print("-" * 20 + " STDOUT " + "-" * 20)
            print(test_run.stdout)
            print("-" * 20 + " STDERR " + "-" * 20)
            print(test_run.stderr)
        else:
            print(f"No test runs found for contribution {contribution_id_str}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(get_latest_failure(sys.argv[1]))
    else:
        print("Please provide a contribution ID")
