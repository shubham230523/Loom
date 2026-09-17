import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.github.client import GitHubClient
from backend.app.api.errors import LoomError, RateLimitError

@pytest.fixture
def client():
    return GitHubClient(access_token="test_token")

@pytest.mark.asyncio
async def test_request_success(client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}
    mock_response.headers = {}

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response

        result = await client.get("/test")
        assert result == {"key": "value"}

@pytest.mark.asyncio
async def test_request_rate_limit(client):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.json.return_value = {"message": "API rate limit exceeded"}
    mock_response.headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Limit": "5000"}

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response

        with pytest.raises(RateLimitError):
            await client.get("/test")

@pytest.mark.asyncio
async def test_request_error(client):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"message": "Not Found"}
    mock_response.headers = {}

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response

        with pytest.raises(LoomError) as exc:
            await client.get("/test")
        assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_request_timeout(client):
    with patch("httpx.AsyncClient.request", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(LoomError, match="timed out"):
            await client.get("/test")

@pytest.mark.asyncio
async def test_request_generic_error(client):
    with patch("httpx.AsyncClient.request", side_effect=httpx.RequestError("fail")):
        with pytest.raises(LoomError, match="request failed"):
            await client.get("/test")

@pytest.mark.asyncio
async def test_handle_error_branches(client):
    mock_response = MagicMock()

    # 1. 401 Unauthorized
    mock_response.status_code = 401
    mock_response.json.return_value = {"message": "Bad credentials"}
    with pytest.raises(LoomError, match="authentication failed"):
        client._handle_error(mock_response)

    # 2. Non-JSON error
    mock_response.status_code = 500
    mock_response.json.side_effect = Exception("Not JSON")
    mock_response.text = "Internal Server Error"
    with pytest.raises(LoomError, match="Internal Server Error"):
        client._handle_error(mock_response)

@pytest.mark.asyncio
async def test_all_methods(client):
    mock_response = MagicMock(status_code=200, content=b"{}")
    mock_response.json.return_value = {}
    mock_response.headers = {}

    with patch("httpx.AsyncClient.request", return_value=mock_response):
        await client.post("/test", json_data={})
        await client.put("/test", json_data={})
        await client.patch("/test", json_data={})
        await client.delete("/test")
