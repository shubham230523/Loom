import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.database.session import SessionLocal
from backend.app.database.models import Repository, RepositoryIndex
from sqlalchemy import select

async def check():
    async with SessionLocal() as db:
        repo = (await db.execute(select(Repository).where(Repository.full_name == "shubham230523/AIMastery"))).scalar_one_or_none()
        if not repo: return

        index = (await db.execute(select(RepositoryIndex).where(RepositoryIndex.repository_id == repo.id).order_by(RepositoryIndex.created_at.desc()))).scalars().first()
        if index:
            print(f"Index Summary: {index.summary}")
        else:
            print("No index found.")

if __name__ == "__main__":
    asyncio.run(check())
