from fastapi import APIRouter, Depends
from backend.app.database import User
from backend.app.security.auth import get_current_user

router = APIRouter()

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "display_name": current_user.display_name,
        "avatar_url": current_user.avatar_url,
        "github_user_id": current_user.github_user_id
    }
