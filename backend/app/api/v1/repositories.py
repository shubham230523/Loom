from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Any
from backend.app.database import get_db, User
from backend.app.security.auth import get_current_user
from backend.app.github.service import github_service
from backend.app.ai import semantic_search_service
from backend.app.repository.issue_service import issue_service
from backend.app.repository.pr_service import pr_service
from backend.app.repository.opportunity_service import opportunity_service
from backend.app.agents.issue_analyzer import issue_analyzer_agent
from backend.app.agents.conflict_detector import conflict_detector_agent
from uuid import UUID

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
    """
    Searches for GitHub repositories using the current user's credentials.
    """
    client = await github_service.get_client_for_user(db, current_user)

    results = await github_service.search_repositories(
        client=client,
        query=q,
        language=language,
        page=page,
        per_page=per_page
    )

    return results

@router.post("/{repository_id}/issues/sync")
async def sync_issues(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Syncs open issues from GitHub to the local database.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)
    count = await issue_service.sync_repository_issues(db, repo, client)

    return {"status": "success", "synced_count": count}

@router.get("/{repository_id}/issues")
async def get_issues(
    repository_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves synced issues for a repository.
    """
    issues = await issue_service.get_repository_issues(
        db=db,
        repository_id=repository_id,
        page=page,
        per_page=per_page
    )
    return issues

@router.get("/{repository_id}/issues/{issue_id}")
async def get_issue_details(
    repository_id: UUID,
    issue_id: UUID,
    include_comments: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves detailed information for a specific issue.
    """
    client = None
    if include_comments:
        client = await github_service.get_client_for_user(db, current_user)

    details = await issue_service.get_issue_details(
        db=db,
        issue_id=issue_id,
        client=client
    )
    return details

@router.post("/{repository_id}/issues/{issue_id}/analyze")
async def analyze_issue(
    repository_id: UUID,
    issue_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Performs AI analysis on a specific issue.
    """
    # 1. Fetch data
    query = select(Issue, Repository).join(Repository).where(
        Issue.id == issue_id,
        Repository.id == repository_id
    )
    result = await db.execute(query)
    row = result.first()

    if not row:
        return {"error": "Issue or Repository not found"}

    issue, repo = row

    # 2. Run Agent
    analysis = await issue_analyzer_agent.analyze_issue(db, issue, repo)

    return analysis

@router.post("/{repository_id}/check-conflicts")
async def check_conflicts(
    repository_id: UUID,
    title: str = Query(...),
    description: str = Query(...),
    files: List[str] = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Checks if a potential opportunity conflicts with existing issues or PRs.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)

    assessment = await conflict_detector_agent.assess_opportunity_conflicts(
        db=db,
        repository=repo,
        client=client,
        title=title,
        description=description,
        affected_files=files
    )

    return assessment

@router.post("/{repository_id}/opportunities/discover")
async def discover_opportunities(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers the autonomous discovery of contribution opportunities.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)
    count = await opportunity_service.discover_and_persist_opportunities(db, repo, client)

    return {"status": "success", "new_opportunities_count": count}

@router.get("/{repository_id}/opportunities")
async def get_opportunities(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the list of identified opportunities for a repository.
    """
    opportunities = await opportunity_service.list_opportunities(db, repository_id)
    return opportunities

@router.get("/{repository_id}/opportunities/{opportunity_id}")
async def get_opportunity_details(
    repository_id: UUID,
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves detailed information for a specific opportunity.
    """
    opportunity = await opportunity_service.get_opportunity_details(db, opportunity_id)

    if not opportunity:
        return {"error": "Opportunity not found"}

    return opportunity

@router.post("/{repository_id}/opportunities/{opportunity_id}/score")
async def score_opportunity(
    repository_id: UUID,
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers AI scoring for a specific opportunity.
    """
    # 1. Fetch Repository and Latest Index
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    index_query = select(RepositoryIndex).where(
        RepositoryIndex.repository_id == repository_id,
        RepositoryIndex.status == "completed"
    ).order_by(RepositoryIndex.created_at.desc())
    index_result = await db.execute(index_query)
    index = index_result.scalar_one_or_none()

    if not index:
        return {"error": "Repository index not found. Please index the repository first."}

    client = await github_service.get_client_for_user(db, current_user)

    # 2. Run scoring
    opportunity = await opportunity_service.score_opportunity(
        db=db,
        opportunity_id=opportunity_id,
        repository=repo,
        index=index,
        client=client
    )

    if not opportunity:
        return {"error": "Opportunity not found"}

    return opportunity

@router.get("/{repository_id}/pulls")
async def get_pull_requests(
    repository_id: UUID,
    state: str = Query("open", regex="^(open|closed|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves pull requests for a repository.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)
    pulls = await pr_service.get_repository_pull_requests(repo, client, state=state)

    return pulls

@router.get("/{repository_id}/pulls/conflicts")
async def detect_pr_conflicts(
    repository_id: UUID,
    files: List[str] = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Detects open PRs that modify the specified files.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)
    conflicts = await pr_service.detect_conflicts(repo, client, files)

    return conflicts

@router.get("/{repository_id}")
async def get_repository_details(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves detailed information for a specific repository.
    """
    client = await github_service.get_client_for_user(db, current_user)

    repository = await github_service.get_repository(
        client=client,
        repo_id=repository_id
    )

    return repository

@router.get("/{repository_id}/search/semantic")
async def semantic_search(
    repository_id: UUID,
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Performs a semantic search within a specific repository.
    """
    results = await semantic_search_service.search(
        db=db,
        repository_id=repository_id,
        query=q,
        limit=limit
    )
    return results

@router.post("/{repository_id}/issues/sync")
async def sync_issues(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Syncs open issues from GitHub to the local database.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)
    count = await issue_service.sync_repository_issues(db, repo, client)

    return {"status": "success", "synced_count": count}

@router.get("/{repository_id}/issues")
async def get_issues(
    repository_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves synced issues for a repository.
    """
    issues = await issue_service.get_repository_issues(
        db=db,
        repository_id=repository_id,
        page=page,
        per_page=per_page
    )
    return issues

@router.get("/{repository_id}/issues/{issue_id}")
async def get_issue_details(
    repository_id: UUID,
    issue_id: UUID,
    include_comments: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves detailed information for a specific issue.
    """
    client = None
    if include_comments:
        client = await github_service.get_client_for_user(db, current_user)

    details = await issue_service.get_issue_details(
        db=db,
        issue_id=issue_id,
        client=client
    )
    return details

@router.post("/{repository_id}/issues/{issue_id}/analyze")
async def analyze_issue(
    repository_id: UUID,
    issue_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Performs AI analysis on a specific issue.
    """
    # 1. Fetch data
    query = select(Issue, Repository).join(Repository).where(
        Issue.id == issue_id,
        Repository.id == repository_id
    )
    result = await db.execute(query)
    row = result.first()

    if not row:
        return {"error": "Issue or Repository not found"}

    issue, repo = row

    # 2. Run Agent
    analysis = await issue_analyzer_agent.analyze_issue(db, issue, repo)

    return analysis

@router.post("/{repository_id}/check-conflicts")
async def check_conflicts(
    repository_id: UUID,
    title: str = Query(...),
    description: str = Query(...),
    files: List[str] = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Checks if a potential opportunity conflicts with existing issues or PRs.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)

    assessment = await conflict_detector_agent.assess_opportunity_conflicts(
        db=db,
        repository=repo,
        client=client,
        title=title,
        description=description,
        affected_files=files
    )

    return assessment

@router.post("/{repository_id}/opportunities/discover")
async def discover_opportunities(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers the autonomous discovery of contribution opportunities.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)
    count = await opportunity_service.discover_and_persist_opportunities(db, repo, client)

    return {"status": "success", "new_opportunities_count": count}

@router.get("/{repository_id}/opportunities")
async def get_opportunities(
    repository_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the list of identified opportunities for a repository.
    """
    opportunities = await opportunity_service.list_opportunities(db, repository_id)
    return opportunities

@router.get("/{repository_id}/opportunities/{opportunity_id}")
async def get_opportunity_details(
    repository_id: UUID,
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves detailed information for a specific opportunity.
    """
    opportunity = await opportunity_service.get_opportunity_details(db, opportunity_id)

    if not opportunity:
        return {"error": "Opportunity not found"}

    return opportunity

@router.post("/{repository_id}/opportunities/{opportunity_id}/score")
async def score_opportunity(
    repository_id: UUID,
    opportunity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers AI scoring for a specific opportunity.
    """
    # 1. Fetch Repository and Latest Index
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    index_query = select(RepositoryIndex).where(
        RepositoryIndex.repository_id == repository_id,
        RepositoryIndex.status == "completed"
    ).order_by(RepositoryIndex.created_at.desc())
    index_result = await db.execute(index_query)
    index = index_result.scalar_one_or_none()

    if not index:
        return {"error": "Repository index not found. Please index the repository first."}

    client = await github_service.get_client_for_user(db, current_user)

    # 2. Run scoring
    opportunity = await opportunity_service.score_opportunity(
        db=db,
        opportunity_id=opportunity_id,
        repository=repo,
        index=index,
        client=client
    )

    if not opportunity:
        return {"error": "Opportunity not found"}

    return opportunity

@router.get("/{repository_id}/pulls")
async def get_pull_requests(
    repository_id: UUID,
    state: str = Query("open", regex="^(open|closed|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves pull requests for a repository.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)
    pulls = await pr_service.get_repository_pull_requests(repo, client, state=state)

    return pulls

@router.get("/{repository_id}/pulls/conflicts")
async def detect_pr_conflicts(
    repository_id: UUID,
    files: List[str] = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Detects open PRs that modify the specified files.
    """
    query = select(Repository).where(Repository.id == repository_id)
    repo_result = await db.execute(query)
    repo = repo_result.scalar_one_or_none()

    if not repo:
        return {"error": "Repository not found"}

    client = await github_service.get_client_for_user(db, current_user)
    conflicts = await pr_service.detect_conflicts(repo, client, files)

    return conflicts
