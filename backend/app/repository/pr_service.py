from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import Repository
from backend.app.github.service import github_service, GitHubClient
from backend.app.utils.logging import logger

class PullRequestService:
    async def get_repository_pull_requests(
        self,
        repository: Repository,
        client: GitHubClient,
        state: str = "open",
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retrieves active pull requests for a repository from GitHub.
        """
        logger.info(f"Fetching {state} pull requests for {repository.full_name}")

        pulls = await github_service.list_pull_requests(
            client=client,
            owner=repository.owner,
            repo=repository.name,
            state=state,
            per_page=min(limit, 100)
        )

        return pulls

    async def detect_conflicts(
        self,
        repository: Repository,
        client: GitHubClient,
        target_files: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Detects open pull requests that modify the same files.
        """
        open_pulls = await self.get_repository_pull_requests(repository, client, state="open")
        conflicting_pulls = []

        for pr in open_pulls:
            try:
                pr_files = await github_service.get_pull_request_files(
                    client=client,
                    owner=repository.owner,
                    repo=repository.name,
                    pull_number=pr["number"]
                )

                pr_file_paths = [f["filename"] for f in pr_files]
                intersection = set(target_files).intersection(set(pr_file_paths))

                if intersection:
                    conflicting_pulls.append({
                        "number": pr["number"],
                        "title": pr["title"],
                        "html_url": pr["html_url"],
                        "conflicting_files": list(intersection),
                        "user": pr["user"]["login"]
                    })
            except Exception as e:
                logger.warning(f"Failed to check files for PR #{pr['number']}: {str(e)}")

        return conflicting_pulls

pr_service = PullRequestService()
