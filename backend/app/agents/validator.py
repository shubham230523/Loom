from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import Contribution, SolutionPlan, CodeReview, TestRun, Repository
from backend.app.github.service import github_service, GitHubClient
from backend.app.security.secret_scanner import secret_scanner
from backend.app.utils.logging import logger

class ValidationIssue(BaseModel):
    category: str = Field(description="security, quality, infrastructure, or process")
    severity: str = Field(description="low, medium, high, or critical")
    message: str
    action_required: bool

class ContributionValidation(BaseModel):
    is_valid: bool
    score: int = Field(ge=0, le=100)
    issues: List[ValidationIssue] = Field(default_factory=list)
    summary: str

class ValidationAgent:
    async def validate_contribution(
        self,
        db: AsyncSession,
        contribution: Contribution,
        repository: Repository,
        client: GitHubClient
    ) -> ContributionValidation:
        """
        Performs comprehensive final validation of a contribution before PR creation.
        """
        logger.info(f"ValidationAgent: Running final check for contribution {contribution.id}")

        issues = []

        # 1. Verify Basic Lifecycle State
        # --- Tests ---
        query = select(TestRun).where(TestRun.contribution_id == contribution.id).order_by(TestRun.timestamp.desc())
        test_res = await db.execute(query)
        latest_test = test_res.scalar_one_or_none()

        if not latest_test or latest_test.status != "success":
            issues.append(ValidationIssue(
                category="quality",
                severity="high",
                message="Tests have not passed for the latest changes.",
                action_required=True
            ))

        # --- Review ---
        query = select(CodeReview).where(CodeReview.contribution_id == contribution.id).order_by(CodeReview.created_at.desc())
        review_res = await db.execute(query)
        latest_review = review_res.scalar_one_or_none()

        if not latest_review or latest_review.decision != "APPROVE":
            issues.append(ValidationIssue(
                category="quality",
                severity="medium",
                message=f"Code review is in {latest_review.decision if latest_review else 'pending'} state.",
                action_required=True
            ))

        # 2. Security & Secrets
        if contribution.diff_summary:
            diff_text = contribution.diff_summary.get("diff", "")
            findings = secret_scanner.scan_text(diff_text)
            if findings:
                issues.append(ValidationIssue(
                    category="security",
                    severity="critical",
                    message=f"Potential secrets detected in the implementation: {len(findings)} matches.",
                    action_required=True
                ))

            # 3. Suspicious Modifications
            suspicious_patterns = [".github/", ".circleci/", ".env", "docker-compose.yml", "id_rsa"]
            changed_files = contribution.diff_summary.get("files", [])
            for f in changed_files:
                if any(p in f for p in suspicious_patterns):
                    issues.append(ValidationIssue(
                        category="security",
                        severity="high",
                        message=f"Suspicious modification to infrastructure or sensitive file: {f}",
                        action_required=True
                    ))

        # 4. Check for Duplicate PRs on GitHub
        try:
            # We search for PRs with similar titles or on the same branch
            existing_prs = await github_service.list_pull_requests(
                client=client,
                owner=repository.owner,
                repo=repository.name,
                state="open"
            )
            for pr in existing_prs:
                if pr["head"]["ref"] == contribution.branch_name:
                    issues.append(ValidationIssue(
                        category="process",
                        severity="medium",
                        message=f"A Pull Request already exists for branch {contribution.branch_name}.",
                        action_required=False
                    ))
                    break
        except Exception as e:
            logger.warning(f"Failed to check for duplicate PRs: {str(e)}")

        # 5. Calculate Validity
        critical_issues = [i for i in issues if i.severity in ["critical", "high"]]
        is_valid = len(critical_issues) == 0

        # Heuristic scoring
        score = 100 - (len(issues) * 10)
        score = max(0, min(100, score))

        summary = "Contribution satisfies all validation criteria." if is_valid else f"Validation failed with {len(critical_issues)} high-severity issues."

        return ContributionValidation(
            is_valid=is_valid,
            score=score,
            issues=issues,
            summary=summary
        )

validation_agent = ValidationAgent()
