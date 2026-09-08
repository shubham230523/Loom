import pytest
from unittest.mock import AsyncMock
from backend.app.database.models import User

@pytest.mark.asyncio
async def test_search_repositories_authenticated(client, mocker, db_session):
    """Verify that search returns results when authenticated."""
    # 1. Create and authenticate a user
    user = User(github_user_id=100, username="auth_user")
    db_session.add(user)
    await db_session.commit()

    # Generate token using session_manager
    from backend.app.security.auth import session_manager
    token = session_manager.create_access_token({"sub": str(user.id)})

    # 2. Mock GitHub search on the instance used by the router
    mocker.patch("backend.app.api.v1.repositories.github_service.get_client_for_user", new_callable=AsyncMock)
    mock_search = mocker.patch("backend.app.api.v1.repositories.github_service.search_repositories", new_callable=AsyncMock)

    mock_search.return_value = {
        "total_count": 1,
        "items": [{"id": 1, "name": "repo1", "full_name": "owner/repo1", "owner": {"login": "owner"}}]
    }

    # 3. Call API
    response = await client.get(
        "/api/v1/repositories/search?q=test",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 1
    assert data["items"][0]["name"] == "repo1"

@pytest.mark.asyncio
async def test_get_repository_details_guest(client, mocker):
    """Verify that guests can view repository details (Phase 4 requirement)."""
    # 1. Mock GitHub response
    mocker.patch("backend.app.api.v1.repositories.github_service.get_client_for_user", new_callable=AsyncMock)
    mock_get = mocker.patch("backend.app.api.v1.repositories.github_service.get_repository", new_callable=AsyncMock)

    mock_get.return_value = {
        "id": 12345,
        "name": "public_repo",
        "full_name": "org/public_repo",
        "owner": {"login": "org", "avatar_url": "http://img"}
    }

    # 2. Call API as guest
    response = await client.get("/api/v1/repositories/12345")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "public_repo"
    assert data["is_imported"] is False
