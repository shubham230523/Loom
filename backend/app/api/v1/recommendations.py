from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from backend.app.database import get_db, User
from backend.app.security.auth import get_current_user
from backend.app.repository.matchmaker import matchmaker_service

router = APIRouter()

@router.get("/")
async def get_recommendations(
    types: Optional[List[str]] = Query(None),
    difficulties: Optional[List[str]] = Query(None),
    languages: Optional[List[str]] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns personalized contribution recommendations.
    """
    return await matchmaker_service.get_recommendations(
        db=db,
        types=types,
        difficulties=difficulties,
        languages=languages
    )
