import re
import json
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import Repository, RepositoryIndex, Opportunity, Issue, Contribution, SolutionPlan, TestRun, CodeReview
from backend.app.repository.service import repository_service, Workspace
from backend.app.github.service import github_service, GitHubClient
from backend.app.agents.solution_planner import solution_planner_agent
from backend.app.agents.implementation import implementation_agent
from backend.app.agents.debugger import debugger_agent
from backend.app.agents.code_reviewer import code_reviewer_agent
from backend.app.security.secret_scanner import secret_scanner
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

    async def execute_implementation(
        self,
        db: AsyncSession,
        contribution_id: UUID,
        client: GitHubClient
    ) -> Dict[str, Any]:
        """
        Triggers the autonomous implementation cycle (Implement -> Test -> Review loop).
        """
        # 1. Fetch context
        query = (
            select(Contribution, Opportunity, Repository, SolutionPlan)
            .join(Opportunity, Contribution.opportunity_id == Opportunity.id)
            .join(Repository, Contribution.repository_id == Repository.id)
            .join(SolutionPlan, Contribution.id == SolutionPlan.contribution_id)
            .where(Contribution.id == contribution_id)
        )
        result = await db.execute(query)
        row = result.first()

        if not row:
            raise LoomError("Contribution, Opportunity, or approved Plan not found", status_code=404)

        contribution, opportunity, repo, plan = row

        if plan.status != "approved":
            raise LoomError("Solution plan must be approved before execution", status_code=400)

        if not contribution.workspace_id:
             raise LoomError("Contribution workspace must be setup before execution", status_code=400)

        # 2. Re-instantiate workspace
        workspace = Workspace(workspace_id=contribution.workspace_id)
        if not workspace.path.exists():
            workspace = await self.setup_contribution_workspace(db, contribution_id, client)

        # 3. Detect technical context
        build_info = await repository_service.detect_build_system(workspace)
        test_info = await repository_service.detect_test_system(workspace, build_info)
        test_command = test_info["test_commands"][0] if test_info["test_commands"] else None

        # 4. Review-Fix Loop
        review_cycles = 0
        max_cycles = settings.MAX_REVIEW_CYCLES
        review_feedback = None
        final_impl_result = None

        while review_cycles <= max_cycles:
            logger.info(f"Review Cycle: Attempt {review_cycles + 1}/{max_cycles + 1}")

            # --- PHASE A: IMPLEMENTATION & DEBUGGING LOOP ---
            retries = 0
            max_retries = settings.MAX_DEBUG_RETRIES
            debugging_context = None

            while retries <= max_retries:
                logger.info(f"Implementation Loop: Attempt {retries + 1}/{max_retries + 1}")

                final_impl_result = await implementation_agent.implement_solution(
                    db=db,
                    repository=repo,
                    plan=plan,
                    contribution=contribution,
                    workspace_path=workspace.path,
                    test_command=test_command,
                    debugging_context=debugging_context,
                    review_feedback=review_feedback
                )

                if final_impl_result.success:
                    break

                if not test_command or retries >= max_retries:
                    break

                # Analyze failure and retry
                query = select(TestRun).where(TestRun.id == final_impl_result.test_run_id)
                res = await db.execute(query)
                test_run = res.scalar_one_or_none()

                if test_run:
                    code_context = ""
                    try:
                        for f in plan.relevant_files[:2]:
                            with open(workspace.path / f, "r") as src:
                                code_context += f"File {f}:\n{src.read()[-2000:]}\n\n"
                    except Exception: pass

                    analysis = await debugger_agent.analyze_failure(
                        test_run=test_run,
                        plan_context=plan.problem,
                        code_context=code_context
                    )
                    debugging_context = f"FAILURE ANALYSIS: {analysis.root_cause_analysis}\nSUGGESTED FIX: {analysis.suggested_fix}"

                retries += 1

            # --- PHASE B: CODE REVIEW ---
            if not final_impl_result.success:
                logger.error("Implementation phase failed. Skipping review.")
                break

            # Generate diff for reviewer
            diff_info = await repository_service.get_contribution_diff(workspace)
            contribution.diff_summary = diff_info
            await db.commit()

            # Execute Review
            logger.info("Triggering autonomous code review...")
            review_record = await self.run_code_review(db, contribution_id)

            if review_record.decision == "APPROVE":
                logger.info("Autonomous code review approved.")

                # --- PHASE C: SECRET SCANNING ---
                findings = secret_scanner.scan_text(contribution.diff_summary["diff"])
                if findings:
                    logger.error(f"SECURITY ALERT: Potential secrets detected in diff for {contribution_id}!")
                    contribution.status = "failed"
                    # We store the finding info in the diff summary or separate field
                    contribution.diff_summary["security_findings"] = findings
                    await db.commit()
                    return {
                        "success": False,
                        "summary": "Implementation blocked due to potential secrets detected in changes.",
                        "findings": findings
                    }

                contribution.status = "in_progress" # Ready for final human check / PR creation
                await db.commit()
                return final_impl_result.model_dump()

            if review_cycles < max_cycles:
                logger.info(f"Review requested changes: {review_record.summary}")
                review_feedback = f"REVIEW FINDINGS: {review_record.summary}\nISSUES TO FIX: {json.dumps(review_record.review_issues, indent=2)}"
                review_cycles += 1
            else:
                logger.error("Maximum review cycles reached.")
                break

        # Final state update if loop finished without approval
        contribution.status = "failed"
        await db.commit()
        return final_impl_result.model_dump() if final_impl_result else {"success": False, "summary": "Workflow aborted"}

    async def run_code_review(
        self,
        db: AsyncSession,
        contribution_id: UUID
    ) -> CodeReview:
        """
        Orchestrates an autonomous code review for a contribution.
        """
        # 1. Fetch full context
        query = (
            select(Contribution, SolutionPlan)
            .join(SolutionPlan, Contribution.id == SolutionPlan.contribution_id)
            .where(Contribution.id == contribution_id)
        )
        result = await db.execute(query)
        row = result.first()

        if not row:
            raise LoomError("Contribution or approved plan not found", status_code=404)

        contribution, plan = row

        if not contribution.diff_summary:
            raise LoomError("Contribution must have a diff before review", status_code=400)

        # 2. Get latest test run
        query = (
            select(TestRun)
            .where(TestRun.contribution_id == contribution_id)
            .order_by(TestRun.timestamp.desc())
        )
        res = await db.execute(query)
        test_run = res.scalar_one_or_none()

        # 3. Execute Review Agent
        review_result = await code_reviewer_agent.review_changes(
            plan=plan,
            diff=contribution.diff_summary["diff"],
            test_run=test_run
        )

        # 4. Persist Review
        review = CodeReview(
            contribution_id=contribution_id,
            decision=review_result.decision.value,
            summary=review_result.summary,
            review_issues=[issue.model_dump() for issue in review_result.issues],
            confidence=review_result.confidence
        )
        db.add(review)

        # If rejected, we might want to update contribution status
        # but for now we just store the review.

        await db.commit()
        await db.refresh(review)

        logger.info(f"Autonomous review completed for {contribution_id}: {review.decision}")
        return review

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
