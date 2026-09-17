import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.github.service import GitHubService
from backend.app.database import User, GitHubAccount
from backend.app.api.errors import LoomError

@pytest.fixture
def service():
    return GitHubService()

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    return client

@pytest.mark.asyncio
async def test_exchange_code_for_token_success(service):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test_token"}
        mock_post.return_value = mock_response

        token = await service.exchange_code_for_token("test_code")
        assert token == "test_token"

@pytest.mark.asyncio
async def test_exchange_code_for_token_error_status(service):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        with pytest.raises(LoomError) as excinfo:
            await service.exchange_code_for_token("test_code")
        assert "Failed to exchange code for token" in str(excinfo.value)

@pytest.mark.asyncio
async def test_exchange_code_for_token_github_error(service):
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "bad_code", "error_description": "The code is invalid"}
        mock_post.return_value = mock_response

        with pytest.raises(LoomError) as excinfo:
            await service.exchange_code_for_token("test_code")
        assert "GitHub Error: The code is invalid" in str(excinfo.value)

@pytest.mark.asyncio
async def test_get_client_for_user_no_user(service, mock_db):
    client = await service.get_client_for_user(mock_db, None)
    assert client.access_token is None

@pytest.mark.asyncio
async def test_get_client_for_user_success(service, mock_db):
    user = User(id="u1")
    account = GitHubAccount(user_id="u1", access_token_encrypted=b"encrypted")

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = account
    mock_db.execute.return_value = mock_result

    with patch("backend.app.github.service.token_encryption.decrypt", return_value="decrypted"):
        client = await service.get_client_for_user(mock_db, user)
        assert client.access_token == "decrypted"

@pytest.mark.asyncio
async def test_get_client_for_user_no_account(service, mock_db):
    user = User(id="u1")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(LoomError) as excinfo:
        await service.get_client_for_user(mock_db, user)
    assert "User does not have a connected GitHub account" in str(excinfo.value)

@pytest.mark.asyncio
async def test_get_user_profile(service):
    with patch("backend.app.github.service.GitHubClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.get.return_value = {"login": "testuser"}
        MockClient.return_value = mock_client

        profile = await service.get_user_profile("token")
        assert profile["login"] == "testuser"
        mock_client.get.assert_called_with("/user")

@pytest.mark.asyncio
async def test_search_repositories(service, mock_client):
    mock_client.get.return_value = {"items": []}

    # Without language
    await service.search_repositories(mock_client, "query")
    mock_client.get.assert_called_with("/search/repositories", params={
        "q": "query", "page": 1, "per_page": 30, "sort": "stars", "order": "desc"
    })

    # With language
    await service.search_repositories(mock_client, "query", language="python")
    mock_client.get.assert_called_with("/search/repositories", params={
        "q": "query language:python", "page": 1, "per_page": 30, "sort": "stars", "order": "desc"
    })

@pytest.mark.asyncio
async def test_get_repository(service, mock_client):
    mock_client.get.return_value = {"id": 123}
    result = await service.get_repository(mock_client, 123)
    assert result["id"] == 123
    mock_client.get.assert_called_with("/repositories/123")

@pytest.mark.asyncio
async def test_list_issues(service, mock_client):
    mock_client.get.return_value = []

    # Without labels
    await service.list_issues(mock_client, "owner", "repo")
    mock_client.get.assert_called_with("/repos/owner/repo/issues", params={
        "state": "open", "page": 1, "per_page": 30, "sort": "updated", "direction": "desc"
    })

    # With labels
    await service.list_issues(mock_client, "owner", "repo", labels=["bug", "help wanted"])
    mock_client.get.assert_called_with("/repos/owner/repo/issues", params={
        "state": "open", "page": 1, "per_page": 30, "sort": "updated", "direction": "desc",
        "labels": "bug,help wanted"
    })

@pytest.mark.asyncio
async def test_get_issue(service, mock_client):
    mock_client.get.return_value = {"number": 1}
    await service.get_issue(mock_client, "owner", "repo", 1)
    mock_client.get.assert_called_with("/repos/owner/repo/issues/1")

@pytest.mark.asyncio
async def test_get_issue_comments(service, mock_client):
    mock_client.get.return_value = []
    await service.get_issue_comments(mock_client, "owner", "repo", 1)
    mock_client.get.assert_called_with("/repos/owner/repo/issues/1/comments")

@pytest.mark.asyncio
async def test_list_pull_requests(service, mock_client):
    mock_client.get.return_value = []
    await service.list_pull_requests(mock_client, "owner", "repo")
    mock_client.get.assert_called_with("/repos/owner/repo/pulls", params={
        "state": "open", "page": 1, "per_page": 30, "sort": "updated", "direction": "desc"
    })

@pytest.mark.asyncio
async def test_get_pull_request(service, mock_client):
    mock_client.get.return_value = {"number": 1}
    await service.get_pull_request(mock_client, "owner", "repo", 1)
    mock_client.get.assert_called_with("/repos/owner/repo/pulls/1")

@pytest.mark.asyncio
async def test_get_pull_request_files(service, mock_client):
    mock_client.get.return_value = []
    await service.get_pull_request_files(mock_client, "owner", "repo", 1)
    mock_client.get.assert_called_with("/repos/owner/repo/pulls/1/files")

@pytest.mark.asyncio
async def test_create_pull_request(service, mock_client):
    mock_client.post.return_value = {"id": 123}
    result = await service.create_pull_request(mock_client, "owner", "repo", "T", "B", "head")
    assert result["id"] == 123
    mock_client.post.assert_called_once()

@pytest.mark.asyncio
async def test_fork_repository(service, mock_client):
    mock_client.post.return_value = {"id": 456}
    await service.fork_repository(mock_client, "owner", "repo")
    mock_client.post.assert_called_with("/repos/owner/repo/forks")
