import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock
from backend.app.security.auth import SessionManager, decode_token, get_current_user, get_optional_current_user
from backend.app.config import settings
from backend.app.api.errors import AuthenticationError
from backend.app.database.models import User

@pytest.fixture
def manager():
    return SessionManager()

def test_create_access_token(manager):
    data = {"sub": "user123"}
    token = manager.create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 10

def test_decode_token_success(manager):
    data = {"sub": "user123"}
    token = manager.create_access_token(data)
    payload = manager.decode_token(token)
    assert payload["sub"] == "user123"

def test_decode_token_expired(manager):
    data = {"sub": "user123"}
    # Create token that expired 1 hour ago
    token = manager.create_access_token(data, expires_delta=timedelta(hours=-1))
    with pytest.raises(AuthenticationError):
        manager.decode_token(token)

def test_decode_token_invalid(manager):
    with pytest.raises(AuthenticationError):
        manager.decode_token("invalid-token")

def test_standalone_decode_token(manager):
    data = {"sub": "user123"}
    token = manager.create_access_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "user123"

@pytest.mark.asyncio
async def test_get_current_user_success(mocker, manager):
    db = AsyncMock()
    user_id = uuid.uuid4()
    # github_user_id is the correct field name
    user = User(id=user_id, github_user_id=123, username="testuser")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    db.execute.return_value = mock_result

    token = manager.create_access_token({"sub": str(user_id)})
    returned_user = await get_current_user(token, db)

    assert returned_user.id == user_id
    assert returned_user.username == "testuser"

@pytest.mark.asyncio
async def test_get_current_user_no_token():
    with pytest.raises(AuthenticationError, match="Session token missing"):
        await get_current_user(None, AsyncMock())

@pytest.mark.asyncio
async def test_get_current_user_invalid_payload(manager):
    token = manager.create_access_token({"not_sub": 1})
    with pytest.raises(AuthenticationError, match="Invalid session payload"):
        await get_current_user(token, AsyncMock())

@pytest.mark.asyncio
async def test_get_current_user_not_found(mocker, manager):
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result

    user_id = uuid.uuid4()
    token = manager.create_access_token({"sub": str(user_id)})
    with pytest.raises(AuthenticationError, match="User not found"):
        await get_current_user(token, db)

@pytest.mark.asyncio
async def test_get_optional_current_user_success(mocker, manager):
    db = AsyncMock()
    user_id = uuid.uuid4()
    user = User(id=user_id, username="testuser", github_user_id=456)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    db.execute.return_value = mock_result

    token = manager.create_access_token({"sub": str(user_id)})
    returned_user = await get_optional_current_user(token, db)
    assert returned_user.id == user_id

@pytest.mark.asyncio
async def test_get_optional_current_user_no_token():
    assert await get_optional_current_user(None, AsyncMock()) is None

@pytest.mark.asyncio
async def test_get_optional_current_user_invalid_token():
    assert await get_optional_current_user("invalid", AsyncMock()) is None

@pytest.mark.asyncio
async def test_get_optional_current_user_invalid_payload(manager):
    token = manager.create_access_token({"not_sub": 1})
    assert await get_optional_current_user(token, AsyncMock()) is None
