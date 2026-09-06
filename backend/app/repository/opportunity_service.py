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

        # 1. Get Latest Index
        query = select(RepositoryIndex).where(
            RepositoryIndex.repository_id == repository.id,
            RepositoryIndex.status == "completed"
        ).order_by(RepositoryIndex.created_at.desc())
        result = await db.execute(query)
        index = result.scalar_one_or_none()

        if not index:
            logger.warning(f"No index found for {repository.full_name}. Indexing first...")
            # Ideally we'd trigger indexing here, but for now we'll just return
            return 0

        workspace = Workspace()
        try:
            # 2. Setup Workspace & Gather Signals
            await repository_service.clone_repository(
                repo_url=repository.html_url,
                access_token=client.access_token,
                workspace=workspace
            )

            code_signals = await repository_service.detect_code_signals(workspace)
            files_metadata = await repository_service.discover_files(workspace)
            test_gaps = await repository_service.detect_test_gaps(workspace, files_metadata)

            # 3. Gather issues & PRs
            issue_query = select(Issue).where(Issue.repository_id == repository.id)
            issue_result = await db.execute(issue_query)
            issues = list(issue_result.scalars().all())

            existing_prs = await pr_service.get_repository_pull_requests(repository, client)

            # 4. Generate Opportunities via Agent
            proposals = await opportunity_generator_agent.generate_opportunities(
                db=db,
                repository=repository,
                index=index,
                issues=issues,
                code_signals=code_signals,
                test_gaps=test_gaps,
                existing_prs=existing_prs
            )

            # 5. Persist to DB (Replace existing pending opportunities)
            # await db.execute(delete(Opportunity).where(
            #    Opportunity.repository_id == repository.id,
            #    Opportunity.status == "pending"
            # ))

            new_count = 0
            for prop in proposals:
                # Basic dedup check (optional)

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

            await db.commit()
            logger.info(f"OpportunityService: Persisted {new_count} new opportunities for {repository.full_name}")
            return new_count

        except Exception as e:
            logger.error(f"Failed to discover opportunities: {str(e)}")
            await db.rollback()
            return 0
        finally:
            await workspace.cleanup()

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
