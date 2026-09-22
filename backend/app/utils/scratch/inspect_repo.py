import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from sqlalchemy import select
from backend.app.database import SessionLocal, Repository
from uuid import UUID

async def get_repo_info(repo_id_str: str):
    repo_id = UUID(repo_id_str)
    async with SessionLocal() as db:
        query = select(Repository).where(Repository.id == repo_id)
        result = await db.execute(query)
        repo = result.scalar_one_or_none()

        if repo:
            print(f"Full Name: {repo.full_name}")
            print(f"HTML URL: {repo.html_url}")
        else:
            print(f"No repository found for {repo_id_str}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(get_repo_info(sys.argv[1]))
