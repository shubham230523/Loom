from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Any
from backend.app.database import get_db, User
from backend.app.security.auth import get_current_user
from backend.app.github.service import github_service

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
