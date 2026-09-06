from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.ai import ai_gateway, ChatRequest, ChatMessage, MessageRole, TaskType, semantic_search_service
from backend.app.repository.pr_service import pr_service
from backend.app.github.service import GitHubClient
from backend.app.database import Repository
from backend.app.utils.logging import logger

class ConflictAssessment(BaseModel):
    risk_level: str = Field(description="Low, Medium, or High risk of duplication or conflict")
    duplicate_issues: List[Dict[str, Any]] = Field(description="List of highly similar existing issues")
    conflicting_prs: List[Dict[str, Any]] = Field(description="List of open PRs that might conflict")
    reasoning: str = Field(description="Detailed explanation of the risk assessment")
    is_duplicate: bool = Field(description="Whether this opportunity is likely a direct duplicate of existing work")

class ConflictDetectorAgent:
    async def assess_opportunity_conflicts(
        self,
        db: AsyncSession,
        repository: Repository,
        client: GitHubClient,
        title: str,
        description: str,
        affected_files: List[str]
    ) -> ConflictAssessment:
        """
        Analyzes an opportunity against existing issues and PRs to detect duplicates or conflicts.
        """
        logger.info(f"ConflictDetectorAgent: Assessing conflicts for '{title}' in {repository.full_name}")

        # 1. Search for duplicate issues (Semantic Search)
        search_results = await semantic_search_service.search(
            db=db,
            repository_id=repository.id,
            query=f"{title} {description}",
            limit=5
        )

        duplicate_issues = []
        for res in search_results:
            if res["type"] == "issue":
                # Only include if semantic score is high enough (heuristic)
                if res.get("score", 0) > 0.7:
                    duplicate_issues.append(res)

        # 2. Check for PR file-level conflicts
        pr_conflicts = await pr_service.detect_conflicts(repository, client, affected_files)

        # 3. AI comparison for PR context (titles and descriptions)
        # Fetch open PRs to compare titles
        open_prs = await pr_service.get_repository_pull_requests(repository, client, state="open", limit=30)

        pr_context = ""
        if open_prs:
            pr_context = "Open Pull Requests:\n"
            for pr in open_prs:
                pr_context += f"- #{pr['number']}: {pr['title']}\n"

        # 4. Construct Prompt
        prompt = f"""
        You are a senior repository maintainer. Assess if the following new "Contribution Opportunity" is a duplicate of existing work or if it will conflict with active Pull Requests.

        NEW OPPORTUNITY:
        Title: {title}
        Description: {description}
        Target Files: {', '.join(affected_files)}

        EXISTING ISSUES (Found via semantic search):
        {json_to_text(duplicate_issues)}

        ACTIVE PULL REQUESTS:
        {pr_context}

        FILE-LEVEL PR CONFLICTS DETECTED:
        {json_to_text(pr_conflicts)}

        Return a structured assessment. Be cautious: it is better to flag a potential conflict than to ignore it.
        """

        request = ChatRequest(
            messages=[
                ChatMessage(role=MessageRole.SYSTEM, content="You are a vigilant maintainer protecting the repository from duplicate work and merge conflicts."),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
        )

        return await ai_gateway.chat_structured(
            request=request,
            response_model=ConflictAssessment,
            task=TaskType.ISSUE_ANALYSIS # Reusing similar task type
        )

def json_to_text(data: Any) -> str:
    import json
    if not data: return "None found."
    return json.dumps(data, indent=2)

conflict_detector_agent = ConflictDetectorAgent()
