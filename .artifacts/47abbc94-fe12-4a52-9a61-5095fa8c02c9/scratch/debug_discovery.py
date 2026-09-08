import asyncio
import os
import sys

# Add project root to path so 'backend.app' imports work
sys.path.append(os.getcwd())

from backend.app.database.session import SessionLocal
from backend.app.database.models import Repository, Issue, RepositoryFile
from sqlalchemy import select

async def debug_repo():
    async with SessionLocal() as db:
        repo_query = select(Repository).where(Repository.full_name == "shubham230523/AIMastery")
        repo = (await db.execute(repo_query)).scalar_one_or_none()

        if not repo:
            print("Repository not found in database.")
            return

        print(f"--- Repository Info ---")
        print(f"Name: {repo.full_name}")
        print(f"ID: {repo.id}")
        print(f"Discovery Status: {repo.discovery_status}")
        print(f"Discovery Error: {repo.discovery_error}")

        issues_query = select(Issue).where(Issue.repository_id == repo.id)
        issues = (await db.execute(issues_query)).scalars().all()
        print(f"\n--- Cached Issues ({len(issues)}) ---")
        for i in issues:
            print(f"- #{i.number}: {i.title}")

        # Check if indexed files exist
        from app.database.models import RepositoryIndex
        index_query = select(RepositoryIndex).where(RepositoryIndex.repository_id == repo.id).order_by(RepositoryIndex.created_at.desc())
        latest_index = (await db.execute(index_query)).scalars().first()

        if latest_index:
            print(f"\n--- Latest Index ---")
            print(f"Status: {latest_index.status}")
            print(f"Commit: {latest_index.commit_sha}")

            files_query = select(RepositoryFile).where(RepositoryFile.repository_index_id == latest_index.id)
            files = (await db.execute(files_query)).scalars().all()
            print(f"Files Count: {len(files)}")
            for f in files[:10]:
                print(f" - {f.path}")
            if len(files) > 10:
                print(f" ... and {len(files) - 10} more")
        else:
            print("\nNo index found for this repository.")

if __name__ == "__main__":
    asyncio.run(debug_repo())
