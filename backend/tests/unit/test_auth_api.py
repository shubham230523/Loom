import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.main import app
from backend.app.database.models import User, GitHubAccount
from uuid import uuid4

@pytest.mark.asyncio
async def test_github_authorize_api(client):
    with patch("backend.app.api.v1.auth.github.settings") as mock_settings:
        mock_settings.GITHUB_CLIENT_ID = "test_client_id"
        mock_settings.GITHUB_AUTHORIZE_URL = "http://github.com/auth"
        mock_settings.GITHUB_REDIRECT_URI = "http://redir"

        response = await client.get("/api/v1/auth/github/authorize")

        assert response.status_code == 200
        assert "authorization_url" in response.json()
        assert "state" in response.json()

@pytest.mark.asyncio
async def test_github_authorize_api_no_client_id(client):
    with patch("backend.app.api.v1.auth.github.settings") as mock_settings:
        mock_settings.GITHUB_CLIENT_ID = None
        response = await client.get("/api/v1/auth/github/authorize")
        assert response.status_code == 500

@pytest.mark.asyncio
async def test_github_callback_success(client, db_session):
    mock_profile = {"id": 123, "login": "testuser", "name": "Test User", "avatar_url": "url"}

    with patch("backend.app.api.v1.auth.github.github_service", new_callable=AsyncMock) as mock_gh, \
         patch("backend.app.api.v1.auth.github.token_encryption") as mock_enc, \
         patch("backend.app.api.v1.auth.github.session_manager") as mock_sm:

        mock_gh.exchange_code_for_token.return_value = "token123"
        mock_gh.get_user_profile.return_value = mock_profile
        mock_enc.encrypt.return_value = "encrypted_str"
        mock_sm.create_access_token.return_value = "jwt123"

        # 1. New user
        response = await client.get("/api/v1/auth/github/callback?code=abc&state=xyz")
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "testuser"

        # 2. Existing user update
        mock_profile["login"] = "updateduser"
        response = await client.get("/api/v1/auth/github/callback?code=abc&state=xyz")
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "updateduser"

@pytest.mark.asyncio
async def test_github_callback_invalid_state(client):
    from backend.app.api.v1.auth.github import get_redis

    mock_redis = AsyncMock()
    mock_redis.exists.return_value = False

    app.dependency_overrides[get_redis] = lambda: mock_redis

    response = await client.get("/api/v1/auth/github/callback?code=abc&state=bad")
    assert response.status_code == 400
    assert "Invalid or expired state" in response.json()["detail"]

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_github_callback_user_exists(client, db_session):
    unique_gh_id = int(uuid.uuid4().int % 1000000)
    mock_profile = {"id": unique_gh_id, "login": "testuser", "name": "Test User", "avatar_url": "url"}

    # Pre-create user and account
    user = User(github_user_id=unique_gh_id, username="oldname")
    db_session.add(user)
    await db_session.commit()

    account = GitHubAccount(user_id=user.id, github_id=unique_gh_id, access_token_encrypted="old")
    db_session.add(account)
    await db_session.commit()

    with patch("backend.app.api.v1.auth.github.github_service", new_callable=AsyncMock) as mock_gh, \
         patch("backend.app.api.v1.auth.github.token_encryption") as mock_enc, \
         patch("backend.app.api.v1.auth.github.session_manager") as mock_sm:

        mock_gh.exchange_code_for_token.return_value = "token123"
        mock_gh.get_user_profile.return_value = mock_profile
        mock_enc.encrypt.return_value = "new_encrypted"
        mock_sm.create_access_token.return_value = "jwt123"

        response = await client.get("/api/v1/auth/github/callback?code=abc&state=xyz")
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "testuser"

        # Verify account was updated
        await db_session.refresh(account)
        assert account.access_token_encrypted == "new_encrypted"
