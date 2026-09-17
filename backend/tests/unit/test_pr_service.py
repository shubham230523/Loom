import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.repository.pr_service import PullRequestService
from backend.app.database.models import Repository

@pytest.fixture
def pr_svc():
    return PullRequestService()

@pytest.mark.asyncio
async def test_get_repository_pull_requests(pr_svc):
    repo = Repository(owner="o", name="n")
    client = MagicMock()
    with patch("backend.app.repository.pr_service.github_service", new_callable=AsyncMock) as mock_gh:
        mock_gh.list_pull_requests.return_value = [{"number": 1}]
        res = await pr_svc.get_repository_pull_requests(repo, client)
        assert len(res) == 1

@pytest.mark.asyncio
async def test_detect_conflicts(pr_svc):
    repo = Repository(owner="o", name="n")
    client = MagicMock()
    with patch("backend.app.repository.pr_service.github_service", new_callable=AsyncMock) as mock_gh:
        # 1. Success with conflict
        mock_gh.list_pull_requests.return_value = [
            {"number": 1, "title": "T1", "html_url": "U1", "user": {"login": "u1"}}
        ]
        mock_gh.get_pull_request_files.return_value = [{"filename": "f1.py"}]

        res = await pr_svc.detect_conflicts(repo, client, ["f1.py"])
        assert len(res) == 1
        assert res[0]["number"] == 1

        # 2. Success no conflict
        res = await pr_svc.detect_conflicts(repo, client, ["f2.py"])
        assert len(res) == 0

        # 3. Exception in file fetch
        mock_gh.get_pull_request_files.side_effect = Exception("GH Fail")
        res = await pr_svc.detect_conflicts(repo, client, ["f1.py"])
        assert len(res) == 0
