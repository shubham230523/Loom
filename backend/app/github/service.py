import httpx
from typing import Dict, Any, Optional
from backend.app.config import settings
from backend.app.api.errors import LoomError
from backend.app.github.client import GitHubClient
from backend.app.security.encryption import token_encryption
from backend.app.database import User, GitHubAccount
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class GitHubService:
    async def exchange_code_for_token(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.GITHUB_TOKEN_URL,
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
                timeout=10.0
            )

            if response.status_code != 200:
                raise LoomError("Failed to exchange code for token", status_code=400)

            data = response.json()
            if "error" in data:
                raise LoomError(f"GitHub Error: {data.get('error_description', data['error'])}", status_code=400)

            return data["access_token"]

    async def get_client_for_user(self, db: AsyncSession, user: User) -> GitHubClient:
        """
        Retrieves the GitHub access token for a user, decrypts it,
        and returns an authenticated GitHubClient.
        """
        query = select(GitHubAccount).where(GitHubAccount.user_id == user.id)
        result = await db.execute(query)
        account = result.scalar_one_or_none()

        if not account:
            raise LoomError("User does not have a connected GitHub account", status_code=401)

        access_token = token_encryption.decrypt(account.access_token_encrypted)
        return GitHubClient(access_token)

    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        client = GitHubClient(access_token)
        return await client.get("/user")

    async def search_repositories(
        self,
        client: GitHubClient,
        query: str,
        language: Optional[str] = None,
        page: int = 1,
        per_page: int = 30
    ) -> Dict[str, Any]:
        """
        Searches for repositories using the GitHub Search API.
        """
        q = query
        if language:
            q += f" language:{language}"

        params = {
            "q": q,
            "page": page,
            "per_page": per_page,
            "sort": "stars",
            "order": "desc"
        }

        return await client.get("/search/repositories", params=params)

    async def get_repository(
        self,
        client: GitHubClient,
        repo_id: int
    ) -> Dict[str, Any]:
        """
        Retrieves detailed information for a specific repository by its GitHub ID.
        """
        return await client.get(f"/repositories/{repo_id}")

github_service = GitHubService()
