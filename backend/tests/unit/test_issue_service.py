import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.repository.issue_service import IssueService
from backend.app.database import Repository, Issue
import uuid

@pytest.fixture
def issue_service():
    return IssueService()

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    return db

@pytest.mark.asyncio
async def test_sync_repository_issues_new(issue_service, mock_db):
    repo = Repository(id=uuid.uuid4(), owner="o", name="n")
    client = MagicMock()

    mock_issues_data = [
        {
            "id": 123,
            "number": 1,
            "title": "Bug",
            "body": "Fix it",
            "state": "open",
            "user": {"login": "user1"},
            "html_url": "url",
            "labels": [{"name": "bug"}]
        }
    ]

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None # No existing issue
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.issue_service.github_service", new_callable=AsyncMock) as mock_gh, \
         patch("backend.app.repository.issue_service.embedding_service", new_callable=AsyncMock):

        mock_gh.list_issues.return_value = mock_issues_data

        count = await issue_service.sync_repository_issues(mock_db, repo, client)

        assert count == 1
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

@pytest.mark.asyncio
async def test_sync_repository_issues_update_and_skip_pr(issue_service, mock_db):
    repo = Repository(id=uuid.uuid4(), owner="o", name="n")
    client = MagicMock()

    existing_issue = Issue(github_issue_id=123, title="Old Title")

    mock_issues_data = [
        {
            "id": 456,
            "pull_request": {} # Should be skipped
        },
        {
            "id": 123,
            "number": 1,
            "title": "New Title",
            "body": "Fix it",
            "state": "open",
            "user": {"login": "user1"},
            "html_url": "url",
            "labels": []
        }
    ]

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_issue
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.issue_service.github_service", new_callable=AsyncMock) as mock_gh:
        mock_gh.list_issues.return_value = mock_issues_data

        count = await issue_service.sync_repository_issues(mock_db, repo, client)

        assert count == 1 # Only one issue synced, PR was skipped
        assert existing_issue.title == "New Title"

@pytest.mark.asyncio
async def test_get_repository_issues(issue_service, mock_db):
    repository_id = uuid.uuid4()
    mock_issues = [Issue(number=1), Issue(number=2)]

    mock_res = MagicMock()
    mock_res.scalars().all.return_value = mock_issues
    mock_db.execute.return_value = mock_res

    res = await issue_service.get_repository_issues(mock_db, repository_id, labels=["bug"])
    assert len(res) == 2

@pytest.mark.asyncio
async def test_get_issue_details_success(issue_service, mock_db):
    issue_id = uuid.uuid4()
    mock_issue = Issue(id=issue_id, number=1, title="T", body="B", state="open", labels=[], author="a", html_url="u", created_at=MagicMock())
    mock_issue.created_at.isoformat.return_value = "2024-01-01"
    mock_repo = Repository(owner="o", name="n")

    mock_res = MagicMock()
    mock_res.first.return_value = (mock_issue, mock_repo)
    mock_db.execute.return_value = mock_res

    client = MagicMock()
    with patch("backend.app.repository.issue_service.github_service", new_callable=AsyncMock) as mock_gh:
        mock_gh.get_issue_comments.return_value = [{"body": "comment"}]

        data = await issue_service.get_issue_details(mock_db, issue_id, client=client)
        assert data["title"] == "T"
        assert data["comments"] == [{"body": "comment"}]

@pytest.mark.asyncio
async def test_get_issue_details_no_issue(issue_service, mock_db):
    mock_db.execute.return_value = MagicMock(first=lambda: None)
    data = await issue_service.get_issue_details(mock_db, uuid.uuid4())
    assert data == {}

@pytest.mark.asyncio
async def test_get_issue_details_comment_error(issue_service, mock_db):
    issue_id = uuid.uuid4()
    mock_issue = Issue(id=issue_id, number=1, title="T", body="B", state="open", labels=[], author="a", html_url="u", created_at=MagicMock())
    mock_issue.created_at.isoformat.return_value = "2024-01-01"
    mock_repo = Repository(owner="o", name="n")
    mock_db.execute.return_value = MagicMock(first=lambda: (mock_issue, mock_repo))

    client = MagicMock()
    with patch("backend.app.repository.issue_service.github_service", new_callable=AsyncMock) as mock_gh:
        mock_gh.get_issue_comments.side_effect = Exception("GH Error")
        data = await issue_service.get_issue_details(mock_db, issue_id, client=client)
        assert data["comments"] == []
