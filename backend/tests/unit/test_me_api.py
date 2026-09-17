import pytest
from backend.app.main import app
from backend.app.security.auth import get_current_user
from backend.app.database.models import User
import uuid

@pytest.fixture
def auth_client(client):
    user = User(id=uuid.uuid4(), username="me", display_name="Me", github_user_id=123)
    app.dependency_overrides[get_current_user] = lambda: user
    yield client
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_me(auth_client):
    resp = await auth_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "me"

@pytest.mark.asyncio
async def test_logout(client):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
