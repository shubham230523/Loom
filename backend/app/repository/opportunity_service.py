from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.app.database import Repository, RepositoryIndex, Issue, Opportunity
from backend.app.github.service import github_service, GitHubClient
from backend.app.repository.service import repository_service, Workspace
from backend.app.repository.pr_service import pr_service
from backend.app.agents.opportunity_generator import opportunity_generator_agent
from backend.app.agents.scoring_agent import scoring_agent
from backend.app.utils.logging import logger

class OpportunityService:
    async def discover_and_persist_opportunities(
        self,
        db: AsyncSession,
        repository: Repository,
        client: GitHubClient
    ) -> int:
        """
        Orchestrates full opportunity discovery workflow and persists results.
        """
        logger.info(f"OpportunityService: Starting discovery for {repository.full_name}")

        repository.discovery_status = "discovering"
        repository.discovery_error = None
        await db.commit()

        # 1. Get Latest Index
        query = select(RepositoryIndex).where(
            RepositoryIndex.repository_id == repository.id,
            RepositoryIndex.status == "completed"
        ).order_by(RepositoryIndex.created_at.desc())
        result = await db.execute(query)
        index = result.scalar_one_or_none()

        if not index:
            logger.warning(f"OpportunityService: No completed index found for {repository.full_name}.")
            repository.discovery_status = "failed"
            repository.discovery_error = "Repository must be indexed before discovery."
            await db.commit()
            return 0

        workspace = Workspace()
        try:
            # 2. Setup Workspace & Gather Signals
            logger.info(f"OpportunityService: Cloning repository {repository.full_name} for discovery...")
            await repository_service.clone_repository(
                repo_url=repository.html_url,
                access_token=client.access_token,
                workspace=workspace
            )
            logger.info(f"OpportunityService: Repository cloned. Detecting signals...")

            code_signals = await repository_service.detect_code_signals(workspace)
            logger.info(f"OpportunityService: Detected {len(code_signals)} code signals (TODOs, etc).")

            files_metadata = await repository_service.discover_files(workspace)
            test_gaps = await repository_service.detect_test_gaps(workspace, files_metadata)
            logger.info(f"OpportunityService: Detected {len(test_gaps)} test gaps.")

            # 3. Gather issues & PRs
            logger.info(f"OpportunityService: Fetching issues and PRs...")
            issue_query = select(Issue).where(Issue.repository_id == repository.id)
            issue_result = await db.execute(issue_query)
            issues = list(issue_result.scalars().all())
            logger.info(f"OpportunityService: Found {len(issues)} cached issues.")

            existing_prs = await pr_service.get_repository_pull_requests(repository, client)
            logger.info(f"OpportunityService: Found {len(existing_prs)} active pull requests.")

            # 4. Generate Opportunities via Agent
            logger.info(f"OpportunityService: Calling OpportunityGeneratorAgent for {repository.full_name}...")
            try:
                proposals = await opportunity_generator_agent.generate_opportunities(
                    db=db,
                    repository=repository,
                    index=index,
                    issues=issues,
                    code_signals=code_signals,
                    test_gaps=test_gaps,
                    existing_prs=existing_prs
                )
                logger.info(f"OpportunityService: Agent generated {len(proposals)} proposals.")
            except Exception as agent_error:
                logger.error(f"OpportunityService: Agent failed to generate opportunities: {str(agent_error)}")

                # If there are NO signals at all, the AI likely struggled to output the right schema for "nothing found"
                # We can safely return an empty list in this case.
                if not issues and not code_signals and not test_gaps:
                    logger.info("OpportunityService: No signals found and AI failed to follow schema. Proceeding with empty list.")
                    proposals = []
                elif len(code_signals) > 0 or len(issues) > 0:
                     logger.info("OpportunityService: Falling back to basic opportunity generation due to AI error...")
                     proposals = self._generate_fallback_proposals(issues, code_signals)
                else:
                     raise agent_error

            new_count = 0
            for prop in proposals:
                opp = Opportunity(
                    repository_id=repository.id,
                    title=prop.title,
                    description=prop.description,
                    type=prop.type,
                    impact=prop.impact,
                    difficulty=prop.difficulty,
                    confidence=prop.confidence,
                    status="pending"
                )
                db.add(opp)
                new_count += 1

            repository.discovery_status = "completed"
            repository.last_discovery_at = datetime.now(timezone.utc)

            if new_count == 0:
                repository.discovery_error = "No actionable opportunities found in the current repository state."
            else:
                repository.discovery_error = None

            await db.commit()
            logger.info(f"OpportunityService: Successfully persisted {new_count} opportunities.")
            return new_count

        except Exception as e:
            logger.error(f"OpportunityService: Error during discovery: {str(e)}", exc_info=True)
            repository.discovery_status = "failed"
            repository.discovery_error = str(e)
            await db.commit()
            raise e
        finally:
            await workspace.cleanup()

    def _generate_fallback_proposals(self, issues: List[Issue], signals: List[Dict[str, Any]]) -> List[Any]:
        """Generates simple opportunities from raw signals without AI."""
        from backend.app.agents.opportunity_generator import OpportunityProposal
        proposals = []

        # 1. Add from issues
        for issue in issues[:3]:
            proposals.append(OpportunityProposal(
                title=f"Address Issue #{issue.number}: {issue.title}",
                description=f"Implement a solution for the GitHub issue: {issue.title}. Body preview: {(issue.body or '')[:100]}...",
                type="bug" if "bug" in str(issue.labels).lower() else "feature",
                impact="Medium",
                difficulty="Intermediate",
                confidence=0.8,
                evidence_source=f"GitHub Issue #{issue.number}",
                affected_files=[]
            ))

        # 2. Add from TODOs
        for signal in signals[:2]:
            proposals.append(OpportunityProposal(
                title=f"Fix TODO in {signal['path']}",
                description=f"Address the TODO found on line {signal['line']}: {signal['content']}",
                type="refactor",
                impact="Low",
                difficulty="Easy",
                confidence=0.9,
                evidence_source=f"Source code: {signal['path']}",
                affected_files=[signal['path']]
            ))

        return proposals

    async def list_opportunities(
        self,
        db: AsyncSession,
        repository_id: UUID
    ) -> List[Opportunity]:
        query = select(Opportunity).where(Opportunity.repository_id == repository_id).order_by(Opportunity.score.desc(), Opportunity.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_opportunity_details(
        self,
        db: AsyncSession,
        opportunity_id: UUID
    ) -> Optional[Opportunity]:
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def score_opportunity(
        self,
        db: AsyncSession,
        opportunity_id: UUID,
        repository: Repository,
        index: RepositoryIndex,
        client: GitHubClient
    ) -> Optional[Opportunity]:
        """
        Orchestrates scoring for a specific opportunity.
        """
        query = select(Opportunity).where(Opportunity.id == opportunity_id)
        result = await db.execute(query)
        opportunity = result.scalar_one_or_none()

        if not opportunity:
            return None

        # Gather context for scoring
        # 1. Maintainer context (recent PR activity)
        prs = await pr_service.get_repository_pull_requests(repository, client, state="all", limit=20)
        maintainer_context = f"Recent PRs: {len(prs)}. States: {[p['state'] for p in prs[:5]]}"

        # 2. Signals context
        # (For now we assume the description already contains most evidence)
        signals_context = f"Evidence from indexing: {opportunity.type}"

        # 3. Execute Scoring
        score_card = await scoring_agent.score_opportunity(
            repository_name=repository.full_name,
            architecture_summary=index.summary.get("architecture_summary", "Unknown") if index.summary else "Unknown",
            opportunity_title=opportunity.title,
            opportunity_description=opportunity.description,
            signals_context=signals_context,
            maintainer_context=maintainer_context
        )

        # 4. Update and Persist
        opportunity.score = float(score_card.overall_score)
        opportunity.scoring_reasoning = score_card.model_dump()

        await db.commit()
        await db.refresh(opportunity)

        return opportunity

opportunity_service = OpportunityService()
