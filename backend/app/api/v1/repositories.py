from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import Optional, List, Any
from uuid import UUID

from backend.app.database import get_db, User, Repository, RepositoryIndex, Issue, Contribution
from backend.app.security.auth import get_current_user
from backend.app.github.service import github_service
from backend.app.ai import semantic_search_service
from backend.app.repository.issue_service import issue_service
from backend.app.repository.pr_service import pr_service
from backend.app.repository.opportunity_service import opportunity_service
from backend.app.repository.contribution_service import contribution_service
from backend.app.repository.indexer import repository_indexer
from backend.app.agents.issue_analyzer import issue_analyzer_agent
from backend.app.agents.conflict_detector import conflict_detector_agent
from backend.app.utils.logging import logger

router = APIRouter()

@router.get("/search")
async def search_repositories(
    q: str = Query(..., min_length=1),
    language: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Searches for GitHub repositories."""
    client = await github_service.get_client_for_user(db, current_user)
    results = await github_service.search_repositories(
        client=client, query=q, language=language, page=page, per_page=per_page
    )
    return results

@router.get("/{repository_id}")
async def get_repository_details(
    repository_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves detailed info, handling both Loom UUIDs and GitHub IDs."""
    repo = None

    # 1. Try to find by UUID
    try:
        uuid_id = UUID(repository_id)
        query = select(Repository).where(Repository.id == uuid_id)
        result = await db.execute(query)
        repo = result.scalar_one_or_none()
    except ValueError:
        pass

    # 2. Try to find by GitHub ID in DB
    if not repo:
        try:
            github_id = int(repository_id)
            query = select(Repository).where(Repository.github_repo_id == github_id)
            result = await db.execute(query)
            repo = result.scalar_one_or_none()
        except ValueError:
            pass

    if repo:
        # Get latest index status
        index_query = select(RepositoryIndex).where(
            RepositoryIndex.repository_id == repo.id
        ).order_by(desc(RepositoryIndex.created_at)).limit(1)
        index_result = await db.execute(index_query)
        latest_index = index_result.scalar_one_or_none()

        # Fetch fresh metadata from GitHub to ensure stars/avatar are current
        client = await github_service.get_client_for_user(db, current_user)
        try:
            gh_repo = await github_service.get_repository(client, repo.github_repo_id)
            return {
                **gh_repo,
                "loom_id": str(repo.id),
                "is_imported": True,
                "indexing_status": latest_index.status if latest_index else "not_started"
            }
        except Exception:
            # Fallback to DB data if GitHub fails
            return {
                "id": repo.github_repo_id,
                "loom_id": str(repo.id),
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "html_url": repo.html_url,
                "language": repo.language,
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "owner": {"login": repo.owner, "avatar_url": None},
                "is_imported": True,
                "indexing_status": latest_index.status if latest_index else "not_started"
            }

    # 3. Fallback: Fetch from GitHub directly
    try:
        github_id = int(repository_id)
        client = await github_service.get_client_for_user(db, current_user)
        gh_repo = await github_service.get_repository(client, github_id)
        return {
            **gh_repo,
            "loom_id": None,
            "is_imported": False,
            "indexing_status": "not_started"
        }
    except Exception:
        raise HTTPException(status_code=404, detail="Repository not found")

@router.post("/initialize")
async def initialize_repository(
    background_tasks: BackgroundTasks,
    github_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Imports a repository into the local database and starts indexing."""
    query = select(Repository).where(Repository.github_repo_id == github_id)
    result = await db.execute(query)
    repo = result.scalar_one_or_none()

    client = await github_service.get_client_for_user(db, current_user)

    if not repo:
        gh_repo = await github_service.get_repository(client, github_id)
        repo = Repository(
            github_repo_id=github_id,
            owner=gh_repo["owner"]["login"],
            name=gh_repo["name"],
            full_name=gh_repo["full_name"],
            html_url=gh_repo["html_url"],
            description=gh_repo.get("description"),
            default_branch=gh_repo.get("default_branch", "main"),
            language=gh_repo.get("language"),
            stargazers_count=gh_repo.get("stargazers_count", 0),
            forks_count=gh_repo.get("forks_count", 0)
        )
        db.add(repo)
        await db.commit()
        await db.refresh(repo)

    # Start indexing in background
    background_tasks.add_task(
        run_indexing,
        str(repo.id),
        client.access_token
    )

    return repo

# Fix background task db session handling
from backend.app.database.session import SessionLocal

async def run_indexing(repo_id: str, access_token: str):
    """Background task for repository indexing"""
    logger.info(f"Starting background indexing for repository {repo_id}")
    async with SessionLocal() as db:
        try:
            query = select(Repository).where(Repository.id == UUID(repo_id))
            repo = (await db.execute(query)).scalar_one_or_none()
            if repo:
                await repository_indexer.index_repository(db, repo, access_token)
        except Exception as e:
            logger.error(f"Background indexing failed for {repo_id}: {str(e)}")

@router.get("/{repository_id}/opportunities")
async def get_opportunities(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns the list of identified opportunities."""
    return await opportunity_service.list_opportunities(db, repository_id)

@router.post("/{repository_id}/opportunities/discover")
async def discover_opportunities(
    repository_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Triggers autonomous discovery of opportunities. Indexes first if needed."""
    query = select(Repository).where(Repository.id == repository_id)
    result = await db.execute(query)
    repo = result.scalar_one_or_none()
    if not repo: raise HTTPException(status_code=404, detail="Repository not found")

    client = await github_service.get_client_for_user(db, current_user)

    # 1. Check for index
    index_query = select(RepositoryIndex).where(
        RepositoryIndex.repository_id == repo.id,
        RepositoryIndex.status == "completed"
    )
    index = (await db.execute(index_query)).scalar_one_or_none()

    if not index:
        # Check if indexing is already in progress
        active_index_query = select(RepositoryIndex).where(
            RepositoryIndex.repository_id == repo.id,
            RepositoryIndex.status == "in_progress"
        )
        active_index = (await db.execute(active_index_query)).scalar_one_or_none()

        if not active_index:
            logger.info(f"Triggering on-demand indexing for {repo.full_name}")
            background_tasks.add_task(run_indexing, str(repo.id), client.access_token)

        return {"status": "indexing", "message": "Repository is being indexed. Discovery will start automatically after indexing."}

    count = await opportunity_service.discover_and_persist_opportunities(db, repo, client)
    return {"status": "success", "new_opportunities_count": count}

@router.post("/{repository_id}/opportunities/{opportunity_id}/score")
async def score_opportunity(
    repository_id: UUID,
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Triggers AI scoring for an opportunity."""
    query = select(Repository).where(Repository.id == repository_id)
    repo = (await db.execute(query)).scalar_one_or_none()
    if not repo: raise HTTPException(status_code=404, detail="Repository not found")

    index_query = select(RepositoryIndex).where(
        RepositoryIndex.repository_id == repository_id,
        RepositoryIndex.status == "completed"
    ).order_by(RepositoryIndex.created_at.desc())
    index = (await db.execute(index_query)).scalar_one_or_none()
    if not index: raise HTTPException(status_code=400, detail="Repository not indexed")

    client = await github_service.get_client_for_user(db, current_user)
    return await opportunity_service.score_opportunity(db, opportunity_id, repo, index, client)

@router.post("/{repository_id}/contributions")
async def create_contribution(
    repository_id: UUID,
    opportunity_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Starts a new contribution."""
    return await contribution_service.create_contribution(db, current_user.id, repository_id, opportunity_id)

@router.get("/{repository_id}/contributions/{contribution_id}")
async def get_contribution_details(
    repository_id: UUID,
    contribution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves details for a contribution."""
    query = select(Contribution).options(
        selectinload(Contribution.test_runs),
        selectinload(Contribution.code_reviews),
        selectinload(Contribution.solution_plan),
        selectinload(Contribution.repository),
        selectinload(Contribution.opportunity)
    ).where(Contribution.id == contribution_id, Contribution.repository_id == repository_id)
    result = await db.execute(query)
    contribution = result.scalar_one_or_none()
    if not contribution: raise HTTPException(status_code=404, detail="Contribution not found")
    return contribution

@router.post("/{repository_id}/contributions/{contribution_id}/plan")
async def generate_contribution_plan(repository_id: UUID, contribution_id: UUID, db: AsyncSession = Depends(get_db)):
    return await contribution_service.generate_plan(db, contribution_id)

@router.post("/{repository_id}/plans/{plan_id}/approve")
async def approve_contribution_plan(plan_id: UUID, approved: bool = Query(True), db: AsyncSession = Depends(get_db)):
    return await contribution_service.approve_plan(db, plan_id, approved)

@router.post("/{repository_id}/contributions/{contribution_id}/implement")
async def execute_implementation(repository_id: UUID, contribution_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    client = await github_service.get_client_for_user(db, current_user)
    return await contribution_service.execute_implementation(db, contribution_id, client)
