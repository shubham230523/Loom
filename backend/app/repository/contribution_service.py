import re
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import Repository, RepositoryIndex, Opportunity, Issue, Contribution, SolutionPlan
from backend.app.repository.service import repository_service, Workspace
from backend.app.github.service import github_service, GitHubClient
from backend.app.agents.solution_planner import solution_planner_agent
from backend.app.utils.logging import logger
from backend.app.api.errors import LoomError

class ContributionService:
    async def create_contribution(
        self,
        db: AsyncSession,
        user_id: UUID,
        repository_id: UUID,
        opportunity_id: UUID
    ) -> Contribution:
        """
        Creates a new contribution record for a user and opportunity.
        """
        # 1. Verify opportunity exists
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await db.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            raise LoomError("Opportunity not found", status_code=404)

        # 2. Check if user already has a contribution for this opportunity
        query = select(Contribution).where(
            Contribution.user_id == user_id,
            Contribution.opportunity_id == opportunity_id
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # 3. Create record
        contribution = Contribution(
            user_id=user_id,
            repository_id=repository_id,
            opportunity_id=opportunity_id,
            status="started"
        )
        db.add(contribution)
        await db.commit()
        await db.refresh(contribution)

        return contribution

    async def generate_plan(
        self,
        db: AsyncSession,
        contribution_id: UUID
    ) -> SolutionPlan:
        """
        Generates and persists a technical solution plan for a contribution.
        """
        # 1. Fetch full context
        query = (
            select(Contribution, Opportunity, Repository)
            .join(Opportunity, Contribution.opportunity_id == Opportunity.id)
            .join(Repository, Contribution.repository_id == Repository.id)
            .where(Contribution.id == contribution_id)
        )
        result = await db.execute(query)
        row = result.first()

        if not row:
            raise LoomError("Contribution not found", status_code=404)

        contribution, opportunity, repo = row

        # 2. Get Latest Index
        query = (
            select(RepositoryIndex)
            .where(RepositoryIndex.repository_id == repo.id, RepositoryIndex.status == "completed")
            .order_by(RepositoryIndex.created_at.desc())
        )
        result = await db.execute(query)
        index = result.scalar_one_or_none()

        if not index:
             raise LoomError("Repository must be indexed before planning", status_code=400)

        # 3. Check for linked issue
        issue = None
        if opportunity.issue_id:
            query = select(Issue).where(Issue.id == opportunity.issue_id)
            result = await db.execute(query)
            issue = result.scalar_one_or_none()

        # 4. Run Planner Agent
        plan_output = await solution_planner_agent.create_plan(
            db=db,
            repository=repo,
            index=index,
            opportunity=opportunity,
            issue=issue
        )

        # 5. Persist Plan
        # Check if plan already exists for this contribution
        query = select(SolutionPlan).where(SolutionPlan.contribution_id == contribution_id)
        result = await db.execute(query)
        existing_plan = result.scalar_one_or_none()

        if existing_plan:
            existing_plan.problem = plan_output.problem
            existing_plan.root_cause = plan_output.root_cause
            existing_plan.relevant_files = plan_output.relevant_files
            existing_plan.relevant_symbols = plan_output.relevant_symbols
            existing_plan.implementation_steps = plan_output.implementation_steps
            existing_plan.testing_strategy = plan_output.testing_strategy
            existing_plan.risks = plan_output.risks
            existing_plan.expected_diff_size = plan_output.expected_diff_size
            existing_plan.confidence = plan_output.confidence
            plan = existing_plan
        else:
            plan = SolutionPlan(
                contribution_id=contribution_id,
                problem=plan_output.problem,
                root_cause=plan_output.root_cause,
                relevant_files=plan_output.relevant_files,
                relevant_symbols=plan_output.relevant_symbols,
                implementation_steps=plan_output.implementation_steps,
                testing_strategy=plan_output.testing_strategy,
                risks=plan_output.risks,
                expected_diff_size=plan_output.expected_diff_size,
                confidence=plan_output.confidence
            )
            db.add(plan)

        contribution.status = "in_progress"
        await db.commit()
        await db.refresh(plan)

        return plan

    async def setup_contribution_workspace(
        self,
        db: AsyncSession,
        contribution_id: UUID,
        client: GitHubClient
    ) -> Workspace:
        """
        Full orchestration of setting up a clean workspace and branch for a contribution.
        """
        # 1. Fetch data
        query = (
            select(Contribution, Opportunity, Repository)
            .join(Opportunity, Contribution.opportunity_id == Opportunity.id)
            .join(Repository, Contribution.repository_id == Repository.id)
            .where(Contribution.id == contribution_id)
        )
        result = await db.execute(query)
        row = result.first()
        if not row:
            raise LoomError("Contribution not found", status_code=404)
        contribution, opportunity, repo = row

        # 2. Check if plan is approved
        query = select(SolutionPlan).where(SolutionPlan.contribution_id == contribution_id)
        result = await db.execute(query)
        plan = result.scalar_one_or_none()
        if not plan or plan.status != "approved":
            raise LoomError("Solution plan must be approved before workspace setup", status_code=400)

        # 3. Create branch name
        # ai/<issue-number>-<short-description>
        clean_title = re.sub(r'[^a-zA-Z0-9]', '-', opportunity.title.lower())[:30].strip('-')
        # If opportunity has an issue, try to get the real issue number
        issue_number = "task"
        if opportunity.issue_id:
            query = select(Issue).where(Issue.id == opportunity.issue_id)
            res = await db.execute(query)
            issue = res.scalar_one_or_none()
            if issue:
                issue_number = str(issue.number)

        branch_name = f"ai/{issue_number}-{clean_title}"

        # 4. Workspace Lifecycle
        workspace = Workspace()
        try:
            await repository_service.clone_repository(
                repo_url=repo.html_url,
                access_token=client.access_token,
                workspace=workspace
            )

            await repository_service.create_contribution_branch(workspace, branch_name)

            # 5. Update contribution record
            contribution.branch_name = branch_name
            contribution.workspace_id = workspace.id
            contribution.status = "in_progress"
            await db.commit()

            return workspace
        except Exception as e:
            await workspace.cleanup()
            raise e

    async def approve_plan(
        self,
        db: AsyncSession,
        plan_id: UUID,
        approved: bool = True
    ) -> SolutionPlan:
        """
        Approves or rejects a technical solution plan.
        """
        query = select(SolutionPlan).where(SolutionPlan.id == plan_id)
        result = await db.execute(query)
        plan = result.scalar_one_or_none()

        if not plan:
            raise LoomError("Solution plan not found", status_code=404)

        plan.status = "approved" if approved else "rejected"
        await db.commit()
        await db.refresh(plan)
        return plan

contribution_service = ContributionService()
