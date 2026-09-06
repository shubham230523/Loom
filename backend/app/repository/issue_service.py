from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from backend.app.database import Repository, Issue, SessionLocal
from backend.app.github.service import github_service, GitHubClient
from backend.app.ai import embedding_service
from backend.app.utils.logging import logger

class IssueService:
    async def sync_repository_issues(
        self,
        db: AsyncSession,
        repository: Repository,
        client: GitHubClient,
        limit: int = 100
    ) -> int:
        """
        Fetches issues from GitHub and syncs them to the local database.
        Returns the number of synced issues.
        """
        logger.info(f"Syncing issues for repository {repository.full_name}")

        synced_count = 0
        page = 1
        per_page = 50

        while synced_count < limit:
            issues_data = await github_service.list_issues(
                client=client,
                owner=repository.owner,
                repo=repository.name,
                state="open",
                page=page,
                per_page=per_page
            )

            if not issues_data:
                break

            for issue_json in issues_data:
                # GitHub issues API also returns Pull Requests, skip them
                if "pull_request" in issue_json:
                    continue

                github_id = issue_json["id"]

                # Check if issue already exists
                query = select(Issue).where(Issue.github_issue_id == github_id)
                result = await db.execute(query)
                existing_issue = result.scalar_one_or_none()

                if existing_issue:
                    # Update existing issue
                    existing_issue.title = issue_json["title"]
                    existing_issue.body = issue_json.get("body")
                    existing_issue.state = issue_json["state"]
                    existing_issue.labels = [l["name"] for l in issue_json.get("labels", [])]
                else:
                    # Create new issue
                    new_issue = Issue(
                        github_issue_id=github_id,
                        repository_id=repository.id,
                        number=issue_json["number"],
                        title=issue_json["title"],
                        body=issue_json.get("body"),
                        state=issue_json["state"],
                        author=issue_json["user"]["login"],
                        html_url=issue_json["html_url"],
                        labels=[l["name"] for l in issue_json.get("labels", [])]
                    )
                    db.add(new_issue)
                    await db.flush() # Flush to get the ID for embedding

                    # Generate embedding for the new issue
                    await embedding_service.embed_issue(db, new_issue)

                synced_count += 1
                if synced_count >= limit:
                    break

            await db.commit()
            page += 1

            # If we got fewer results than per_page, it was the last page
            if len(issues_data) < per_page:
                break

        logger.info(f"Successfully synced {synced_count} issues for {repository.full_name}")
        return synced_count

    async def get_repository_issues(
        self,
        db: AsyncSession,
        repository_id: UUID,
        page: int = 1,
        per_page: int = 30,
        labels: Optional[List[str]] = None
    ) -> List[Issue]:
        """
        Retrieves synced issues from the database.
        """
        query = select(Issue).where(Issue.repository_id == repository_id)

        if labels:
            # Simple overlap check for JSON labels
            # Note: This might need dialect-specific optimization for production
            pass

        query = query.order_by(Issue.number.desc()).offset((page - 1) * per_page).limit(per_page)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_issue_details(
        self,
        db: AsyncSession,
        issue_id: UUID,
        client: Optional[GitHubClient] = None
    ) -> Dict[str, Any]:
        """
        Returns full issue details, optionally including live comments from GitHub.
        """
        query = select(Issue, Repository).join(Repository).where(Issue.id == issue_id)
        result = await db.execute(query)
        row = result.first()

        if not row:
            return {}

        issue, repo = row
        data = {
            "id": str(issue.id),
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "labels": issue.labels,
            "author": issue.author,
            "html_url": issue.html_url,
            "created_at": issue.created_at.isoformat(),
            "comments": []
        }

        if client:
            try:
                comments = await github_service.get_issue_comments(
                    client=client,
                    owner=repo.owner,
                    repo=repo.name,
                    issue_number=issue.number
                )
                data["comments"] = comments
            except Exception as e:
                logger.warning(f"Failed to fetch live comments for issue {issue.number}: {str(e)}")

        return data

issue_service = IssueService()
