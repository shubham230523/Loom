import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from backend.app.database.session import SessionLocal
from backend.app.database.models import Repository, GitHubAccount
from backend.app.github.client import GitHubClient
from sqlalchemy import select

async def debug_github():
    async with SessionLocal() as db:
        repo_query = select(Repository).where(Repository.full_name == "shubham230523/AIMastery")
        repo = (await db.execute(repo_query)).scalar_one_or_none()

        if not repo:
            print("Repository not found in database.")
            return

        print(f"Repo: {repo.full_name}")

        # Get token from GitHubAccount
        account_query = select(GitHubAccount).order_by(GitHubAccount.created_at.desc())
        account = (await db.execute(account_query)).scalars().first()

        if not account:
            print("No GitHub account found.")
            return

        # Access token is encrypted in DB, but for debug we might have it in .env or we can decrypt
        # For now, let's try to list issues directly via GitHub service
        from backend.app.github.service import github_service
        client = await github_service.get_client_for_user(db, None) # Might fail without user

        # Try to use client if we have one
        try:
            gh_repo = await github_service.get_repository(client, repo.github_repo_id)
            print(f"GitHub Stars: {gh_repo.get('stargazers_count')}")

            issues = await client.get(f"/repos/{repo.full_name}/issues", params={"state": "all"})
            print(f"Total Issues (API): {len(issues)}")
            for i in issues[:5]:
                 print(f" - #{i['number']}: {i['title']} ({i['state']})")

            contents = await client.get(f"/repos/{repo.full_name}/contents")
            print(f"Root Contents:")
            for c in contents:
                print(f" - {c['path']} ({c['type']})")
        except Exception as e:
            print(f"Error calling GitHub: {e}")

if __name__ == "__main__":
    asyncio.run(debug_github())
