import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.database.session import SessionLocal
from backend.app.database.models import Repository, Opportunity
from backend.app.github.client import GitHubClient
from backend.app.repository.opportunity_service import opportunity_service
from sqlalchemy import select, delete

async def test_discovery():
    async with SessionLocal() as db:
        repo_query = select(Repository).where(Repository.full_name == "shubham230523/AIMastery")
        repo = (await db.execute(repo_query)).scalar_one_or_none()

        if not repo:
            print("Repository not found.")
            return

        # Clear old opportunities to start fresh
        await db.execute(delete(Opportunity).where(Opportunity.repository_id == repo.id))
        await db.commit()

        print(f"Running discovery for {repo.full_name}...")

        # We need a token
        from backend.app.database.models import GitHubAccount
        account = (await db.execute(select(GitHubAccount).order_by(GitHubAccount.created_at.desc()))).scalars().first()
        client = GitHubClient(access_token="fake" if not account else None) # Use actual logic if possible

        from backend.app.github.service import github_service
        client = await github_service.get_client_for_user(db, None)

        count = await opportunity_service.discover_and_persist_opportunities(db, repo, client)

        print(f"Discovery complete. Found {count} opportunities.")

        opps_query = select(Opportunity).where(Opportunity.repository_id == repo.id)
        opps = (await db.execute(opps_query)).scalars().all()
        for o in opps:
            print(f" - [{o.type}] {o.title}")
            print(f"   {o.description[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_discovery())
