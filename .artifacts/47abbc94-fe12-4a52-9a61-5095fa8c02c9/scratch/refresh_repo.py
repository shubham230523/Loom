import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.database.session import SessionLocal
from backend.app.database.models import Repository, GitHubAccount, RepositoryIndex
from backend.app.repository.service import repository_service, Workspace
from backend.app.repository.analyzer import repository_analyzer
from sqlalchemy import select

async def refresh():
    async with SessionLocal() as db:
        repo_query = select(Repository).where(Repository.full_name == "shubham230523/AIMastery")
        repo = (await db.execute(repo_query)).scalar_one_or_none()

        if not repo:
            print("Repository not found.")
            return

        print(f"Refreshing index for {repo.full_name}...")

        # Get token
        account_query = select(GitHubAccount).order_by(GitHubAccount.created_at.desc())
        account = (await db.execute(account_query)).scalars().first()

        if not account:
            print("No GitHub account found.")
            return

        from backend.app.github.service import github_service
        client = await github_service.get_client_for_user(db, None)

        workspace = Workspace()
        await repository_service.clone_repository(repo.html_url, client.access_token, workspace)

        index = (await db.execute(select(RepositoryIndex).where(RepositoryIndex.repository_id == repo.id).order_by(RepositoryIndex.created_at.desc()))).scalars().first()

        if not index:
             print("No index record found to update.")
             return

        print("Updating index summary...")
        await repository_analyzer.update_index_summary(db, index, workspace)

        await db.commit()
        await db.refresh(index)
        print(f"Indexing completed. Summary exists: {index.summary is not None}")
        if index.summary:
            print(f"Summary: {index.summary.get('architecture_summary')[:100]}...")
        await workspace.cleanup()

if __name__ == "__main__":
    asyncio.run(refresh())
