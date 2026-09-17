import pytest
from unittest.mock import AsyncMock, patch
from backend.app.services.redis import RedisService

@pytest.fixture
def service():
    return RedisService()

@pytest.mark.asyncio
async def test_redis_connect_success(service):
    with patch("backend.app.services.redis.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_from_url.return_value = mock_redis

        await service.connect()
        assert service.client == mock_redis
        mock_redis.ping.assert_called_once()

@pytest.mark.asyncio
async def test_redis_get_set(service):
    mock_redis = AsyncMock()
    service._redis = mock_redis

    await service.set("key", "value", expire=10)
    mock_redis.set.assert_called_with("key", "value", ex=10)

    mock_redis.get.return_value = "value"
    val = await service.get("key")
    assert val == "value"

@pytest.mark.asyncio
async def test_redis_disconnect(service):
    mock_redis = AsyncMock()
    service._redis = mock_redis
    await service.disconnect()
    mock_redis.close.assert_called_once()

@pytest.mark.asyncio
async def test_redis_connect_no_url(service):
    with patch("backend.app.services.redis.settings") as mock_settings:
        mock_settings.REDIS_URL = None
        await service.connect()
        assert service.client is None

@pytest.mark.asyncio
async def test_redis_connect_failure(service):
    with patch("backend.app.services.redis.from_url") as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = Exception("Connect Fail")
        mock_from_url.return_value = mock_redis

        await service.connect()
        assert service.client is None

@pytest.mark.asyncio
async def test_redis_ops_no_client(service):
    # Tests branches where self._redis is None
    assert await service.get("key") is None
    assert await service.set("key", "val") is None
