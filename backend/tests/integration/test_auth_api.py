import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_github_authorize_returns_url(client):
    """Verify that authorize endpoint returns a valid GitHub URL and state."""
    response = await client.get("/api/v1/auth/github/authorize")
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert "state" in data
    assert "github.com/login/oauth/authorize" in data["authorization_url"]

@pytest.mark.asyncio
async def test_github_callback_success(client, mocker, db_session):
    """Verify successful OAuth callback creates a user and session."""
    # 1. Mock GitHub service instance methods
    mock_exchange = mocker.patch("backend.app.api.v1.auth.github.github_service.exchange_code_for_token", new_callable=AsyncMock)
    mock_profile = mocker.patch("backend.app.api.v1.auth.github.github_service.get_user_profile", new_callable=AsyncMock)

    mock_exchange.return_value = "fake_token"
    mock_profile.return_value = {
        "id": 999,
        "login": "gh_test_user",
        "name": "GitHub Tester",
        "avatar_url": "http://avatar.url"
    }

    # 2. Call callback endpoint
    # We skip state validation by not providing redis or mocking it if needed,
    # but in our conftest we didn't mock redis.
    # Let's check backend/app/api/v1/auth/github.py: it checks `if redis:`.
    # In tests, get_redis might return None if not configured.

    response = await client.get("/api/v1/auth/github/callback?code=123&state=abc")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "access_token" in data
    assert data["user"]["username"] == "gh_test_user"

@pytest.mark.asyncio
async def test_get_me_unauthorized(client):
    """Verify that /me requires authentication."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"
