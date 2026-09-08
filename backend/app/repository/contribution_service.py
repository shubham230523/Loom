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
from backend.app.agents.validator import validation_agent
from backend.app.security.secret_scanner import secret_scanner
from backend.app.services.agent_run_service import agent_run_service
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

        # 1.5 Create Agent Run
        agent_run = await agent_run_service.create_agent_run(db, contribution_id, "planner")

        try:
            # 2. Get Latest Index
            await agent_run_service.emit_event(db, agent_run.id, "step_started", "Fetching project context...")
            query = (
                select(RepositoryIndex)
                .where(RepositoryIndex.repository_id == repo.id, RepositoryIndex.status == "completed")
                .order_by(RepositoryIndex.created_at.desc())
                .limit(1)
            )
            index = (await db.execute(query)).scalars().first()

            if not index:
                 raise LoomError("Repository must be indexed before planning", status_code=400)

            await agent_run_service.emit_event(db, agent_run.id, "step_completed", "Context retrieved.")

            # 3. Check for linked issue
            issue = None
            if opportunity.issue_id:
                query = select(Issue).where(Issue.id == opportunity.issue_id)
                result = await db.execute(query)
                issue = result.scalar_one_or_none()

            # 4. Run Planner Agent
            await agent_run_service.emit_event(db, agent_run.id, "step_started", "Synthesizing solution blueprint...")
            plan_output = await solution_planner_agent.create_plan(
                db=db,
                repository=repo,
                index=index,
                opportunity=opportunity,
                issue=issue
            )
            await agent_run_service.emit_event(db, agent_run.id, "step_completed", "Solution blueprint generated.")

            # 5. Persist Plan
            # ...

            # ... (rest of plan logic)

            await agent_run_service.emit_event(db, agent_run.id, "approval_required", "Solution plan ready for review.")
            await agent_run_service.complete_run(db, agent_run.id, success=True)

            return {
                "agent_run_id": str(agent_run.id),
                "plan": plan
            }
        except Exception as e:
            await agent_run_service.emit_event(db, agent_run.id, "failed", f"Planning failed: {str(e)}")
            await agent_run_service.complete_run(db, agent_run.id, success=False)
            raise e

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

        # 4. Create Agent Run for tracking
        agent_run = await agent_run_service.create_agent_run(db, contribution_id, "coder")

        # 5. Re-instantiate workspace
        workspace = Workspace(workspace_id=contribution.workspace_id)
        if not workspace.path.exists():
            await agent_run_service.emit_event(db, agent_run.id, "step_started", "Restoring workspace...")
            workspace = await self.setup_contribution_workspace(db, contribution_id, client)
            await agent_run_service.emit_event(db, agent_run.id, "step_completed", "Workspace restored.")

        # 6. Detect technical context
        build_info = await repository_service.detect_build_system(workspace)
        test_info = await repository_service.detect_test_system(workspace, build_info)
        test_command = test_info["test_commands"][0] if test_info["test_commands"] else None

        # 7. Review-Fix Loop
        review_cycles = 0
        max_cycles = settings.MAX_REVIEW_CYCLES
        review_feedback = None
        final_impl_result = None

        try:
            while review_cycles <= max_cycles:
                logger.info(f"Review Cycle: Attempt {review_cycles + 1}/{max_cycles + 1}")
                await agent_run_service.emit_event(db, agent_run.id, "step_started", f"Starting review cycle {review_cycles + 1}")

                # --- PHASE A: IMPLEMENTATION & DEBUGGING LOOP ---
                retries = 0
                max_retries = settings.MAX_DEBUG_RETRIES
                debugging_context = None

                while retries <= max_retries:
                    logger.info(f"Implementation Loop: Attempt {retries + 1}/{max_retries + 1}")
                    await agent_run_service.emit_event(db, agent_run.id, "step_started", f"Applying implementation changes (Attempt {retries + 1})")

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

                    for f in final_impl_result.files_modified:
                        await agent_run_service.emit_event(db, agent_run.id, "file_changed", f"Modified {f}", {"path": f})

                    if final_impl_result.success:
                        await agent_run_service.emit_event(db, agent_run.id, "test_completed", "Implementation tests passed.")
                        break

                    if not test_command:
                        await agent_run_service.emit_event(db, agent_run.id, "test_completed", "No tests found for validation.")
                        break

                    if retries >= max_retries:
                         await agent_run_service.emit_event(db, agent_run.id, "test_completed", "Tests failed after maximum retries.")
                         break

                    # Analyze failure and retry
                    await agent_run_service.emit_event(db, agent_run.id, "test_completed", "Tests failed. Analyzing failure...")
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
                        await agent_run_service.emit_event(db, agent_run.id, "step_completed", "Failure analysis complete. Retrying implementation.")

                    retries += 1

                # --- PHASE B: CODE REVIEW ---
                if not final_impl_result.success:
                    break

                await agent_run_service.emit_event(db, agent_run.id, "review_started", "Triggering autonomous technical audit.")

                # Generate diff for reviewer
                diff_info = await repository_service.get_contribution_diff(workspace)
                contribution.diff_summary = diff_info
                await db.commit()

                review_record = await self.run_code_review(db, contribution_id)
                await agent_run_service.emit_event(db, agent_run.id, "review_completed", f"Review finished: {review_record.decision}", {"decision": review_record.decision})

                if review_record.decision == "APPROVE":
                    # --- PHASE C: SECRET SCANNING ---
                    await agent_run_service.emit_event(db, agent_run.id, "step_started", "Scanning for potential secrets...")
                    findings = secret_scanner.scan_text(contribution.diff_summary["diff"])
                    if findings:
                        await agent_run_service.emit_event(db, agent_run.id, "failed", f"Security Alert: {len(findings)} potential secrets detected.")
                        contribution.status = "failed"
                        contribution.diff_summary["security_findings"] = findings
                        await db.commit()
                        await agent_run_service.complete_run(db, agent_run.id, success=False)
                        return {"success": False, "findings": findings}

                    await agent_run_service.emit_event(db, agent_run.id, "step_completed", "Secret scan passed.")
                    contribution.status = "in_progress"
                    await db.commit()
                    await agent_run_service.complete_run(db, agent_run.id, success=True)
                    return {
                        "agent_run_id": str(agent_run.id),
                        "result": final_impl_result.model_dump()
                    }

                if review_cycles < max_cycles:
                    review_feedback = f"REVIEW FINDINGS: {review_record.summary}\nISSUES TO FIX: {json.dumps(review_record.review_issues, indent=2)}"
                    review_cycles += 1
                else:
                    break

            contribution.status = "failed"
            await db.commit()
            await agent_run_service.complete_run(db, agent_run.id, success=False)
            return final_impl_result.model_dump() if final_impl_result else {"success": False}
        except Exception as e:
            await agent_run_service.emit_event(db, agent_run.id, "failed", f"Unexpected error: {str(e)}")
            await agent_run_service.complete_run(db, agent_run.id, success=False)
            raise e

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

    async def validate_contribution(
        self,
        db: AsyncSession,
        contribution_id: UUID,
        client: GitHubClient
    ) -> Any:
        """
        Runs the final validation suite for a contribution.
        """
        # Fetch context
        query = (
            select(Contribution, Repository)
            .join(Repository)
            .where(Contribution.id == contribution_id)
        )
        result = await db.execute(query)
        row = result.first()

        if not row:
            raise LoomError("Contribution not found", status_code=404)

        contribution, repo = row

        # Run validation agent
        return await validation_agent.validate_contribution(db, contribution, repo, client)

    async def push_to_github(
        self,
        db: AsyncSession,
        contribution_id: UUID,
        client: GitHubClient
    ) -> Dict[str, str]:
        """
        Performs the actual git push of the contribution branch to GitHub.
        """
        # 1. Fetch context
        query = (
            select(Contribution, Repository)
            .join(Repository)
            .where(Contribution.id == contribution_id)
        )
        result = await db.execute(query)
        row = result.first()
        if not row:
            raise LoomError("Contribution not found", status_code=404)
        contribution, repo = row

        # 2. Safety Checks
        if contribution.branch_name == repo.default_branch:
            raise LoomError("Safety breach: Attempted to push directly to the default branch", status_code=403)

        if not contribution.workspace_id:
            raise LoomError("Contribution has no associated workspace", status_code=400)

        # 3. Perform Push
        workspace = Workspace(workspace_id=contribution.workspace_id)
        if not workspace.path.exists():
             # We might need to re-implement/restore workspace here in production
             raise LoomError("Workspace no longer exists. Contribution must be re-implemented.", status_code=400)

        await repository_service.push_contribution(
            workspace=workspace,
            branch_name=contribution.branch_name,
            access_token=client.access_token,
            repo_url=repo.html_url
        )

        return {
            "status": "success",
            "branch": contribution.branch_name,
            "repository": repo.full_name
        }

    async def create_github_pr(
        self,
        db: AsyncSession,
        contribution_id: UUID,
        client: GitHubClient
    ) -> Dict[str, Any]:
        """
        Orchestrates the creation of a Pull Request on GitHub.
        """
        # 1. Fetch context with all relevant details
        query = (
            select(Contribution, Repository, Opportunity, SolutionPlan)
            .join(Repository, Contribution.repository_id == Repository.id)
            .join(Opportunity, Contribution.opportunity_id == Opportunity.id)
            .outerjoin(SolutionPlan, Contribution.id == SolutionPlan.contribution_id)
            .where(Contribution.id == contribution_id)
        )
        result = await db.execute(query)
        row = result.first()
        if not row:
            raise LoomError("Contribution not found", status_code=404)
        contribution, repo, opportunity, plan = row

        if not contribution.branch_name:
            raise LoomError("Branch must be pushed before PR creation", status_code=400)

        # 2. Fetch latest test run
        query = select(TestRun).where(TestRun.contribution_id == contribution_id).order_by(TestRun.timestamp.desc()).limit(1)
        latest_test = (await db.execute(query)).scalars().first()

        # 3. Construct PR Body
        pr_body = self._generate_pr_body(opportunity, plan, latest_test)

        # 4. Create PR on GitHub
        try:
            pr_data = await github_service.create_pull_request(
                client=client,
                owner=repo.owner,
                repo=repo.name,
                title=f"Loom: {opportunity.title}",
                body=pr_body,
                head=contribution.branch_name,
                base=repo.default_branch
            )

            # 5. Update contribution record
            contribution.status = "pull_request_created"
            await db.commit()

            return {
                "id": pr_data["id"],
                "number": pr_data["number"],
                "url": pr_data["html_url"],
                "title": pr_data["title"]
            }
        except Exception as e:
            logger.error(f"Failed to create PR for {contribution_id}: {str(e)}")
            raise LoomError(f"GitHub PR creation failed: {str(e)}", status_code=500)

    def _generate_pr_body(self, opportunity: Opportunity, plan: Optional[SolutionPlan], test_run: Optional[TestRun]) -> str:
        """
        Generates a truthful and comprehensive Pull Request description.
        """
        body = f"## Loom Contribution: {opportunity.title}\n\n"

        if plan:
            body += "### Problem\n"
            body += f"{plan.problem}\n\n"
            body += "### Solution\n"
            body += f"{plan.root_cause}\n\n"
            body += "#### Implementation Steps\n"
            for step in plan.implementation_steps:
                body += f"- {step}\n"
            body += "\n"
        else:
            body += "### Description\n"
            body += f"{opportunity.description}\n\n"

        body += "### Automated Validation\n"
        if test_run:
            status_emoji = "✅" if test_run.status == "success" else "❌"
            body += f"{status_emoji} Tests **{test_run.status.upper()}**\n"
            body += f"- Command: `{test_run.command}`\n"
            body += f"- Duration: {round(test_run.duration, 2)}s\n"
        else:
            body += "⚠️ No automated tests were executed for this contribution.\n"

        body += "\n---\n"
        body += "*Generated by [Loom](https://loom.dev) - Autonomous Collaboration Platform*"

        return body

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
