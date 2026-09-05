import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from urllib.parse import urlencode
from backend.app.config import settings
from backend.app.services.redis import get_redis
from backend.app.database import get_db, User, GitHubAccount
from backend.app.github.service import github_service
from backend.app.security.encryption import token_encryption
from backend.app.security.auth import session_manager
from backend.app.utils.logging import logger
from redis.asyncio import Redis
from typing import Optional

router = APIRouter()

@router.get("/github/authorize")
async def github_authorize(
    redis: Optional[Redis] = Depends(get_redis)
):
    """
    Generates the GitHub OAuth authorization URL.
    Returns the URL and the state parameter for secure validation.
    """
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub client ID not configured"
        )

    # Generate a secure random state
    state = secrets.token_urlsafe(32)

    # Store state in Redis if available for later validation in callback
    if redis:
        # Expire in 10 minutes
        await redis.set(f"auth_state:{state}", "1", ex=600)

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
        "scope": "user:email repo",
        "state": state,
    }

    auth_url = f"{settings.GITHUB_AUTHORIZE_URL}?{urlencode(params)}"

    return {
        "authorization_url": auth_url,
        "state": state
    }

@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str,
    redis: Optional[Redis] = Depends(get_redis),
    db: AsyncSession = Depends(get_db)
):
    """
    Handles the GitHub OAuth callback.
    Exchanges code for token, fetches profile, and creates/updates user.
    """
    # 1. Validate State
    if redis:
        state_exists = await redis.exists(f"auth_state:{state}")
        if not state_exists:
            raise HTTPException(status_code=400, detail="Invalid or expired state")
        await redis.delete(f"auth_state:{state}")

    # 2. Exchange Code for Token
    access_token = await github_service.exchange_code_for_token(code)

    # 3. Fetch User Profile
    profile = await github_service.get_user_profile(access_token)
    github_id = profile["id"]
    username = profile["login"]

    # 4. Find or Create User
    query = select(User).where(User.github_user_id == github_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            github_user_id=github_id,
            username=username,
            display_name=profile.get("name"),
            avatar_url=profile.get("avatar_url")
        )
        db.add(user)
        await db.flush() # Get user.id
        logger.info(f"Created new user: {username}")
    else:
        # Update profile info
        user.username = username
        user.display_name = profile.get("name")
        user.avatar_url = profile.get("avatar_url")
        logger.info(f"Updated existing user: {username}")

    # 5. Securely Store Encrypted Token
    encrypted_token = token_encryption.encrypt(access_token)

    query = select(GitHubAccount).where(GitHubAccount.user_id == user.id)
    result = await db.execute(query)
    github_account = result.scalar_one_or_none()

    if not github_account:
        github_account = GitHubAccount(
            user_id=user.id,
            github_id=github_id,
            access_token_encrypted=encrypted_token
        )
        db.add(github_account)
    else:
        github_account.access_token_encrypted = encrypted_token

    await db.commit()

    # 6. Create Loom Session (JWT)
    session_token = session_manager.create_access_token(data={"sub": str(user.id)})

    return {
        "status": "success",
        "message": f"Successfully authenticated as {username}",
        "access_token": session_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username
        }
    }
