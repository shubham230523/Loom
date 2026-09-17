import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.agents.validator import ValidationAgent, ContributionValidation
from backend.app.database.models import Contribution, Repository, TestRun, CodeReview

@pytest.fixture
def agent():
    return ValidationAgent()

@pytest.mark.asyncio
async def test_validate_contribution_success(agent):
    db = AsyncMock()
    contr_id = uuid.uuid4()
    contribution = Contribution(id=contr_id, branch_name="fix", diff_summary={"diff": "+ code", "files": ["f.py"]})
    repository = Repository(owner="o", name="n")
    client = MagicMock()

    # Mock DB queries
    mock_test = TestRun(status="success")
    mock_review = CodeReview(decision="APPROVE")

    mock_result_test = MagicMock()
    mock_result_test.scalars().first.return_value = mock_test

    mock_result_review = MagicMock()
    mock_result_review.scalars().first.return_value = mock_review

    db.execute.side_effect = [mock_result_test, mock_result_review]

    with patch("backend.app.agents.validator.secret_scanner") as mock_scanner, \
         patch("backend.app.agents.validator.github_service", new_callable=AsyncMock) as mock_gh:

        mock_scanner.scan_text.return_value = []
        mock_gh.list_pull_requests.return_value = []

        validation = await agent.validate_contribution(db, contribution, repository, client)

        assert validation.is_valid is True
        assert validation.score == 100
        assert len(validation.issues) == 0

@pytest.mark.asyncio
async def test_validate_contribution_failed_test(agent):
    db = AsyncMock()
    contribution = Contribution(id=uuid.uuid4())
    repository = Repository(owner="o", name="n")
    client = MagicMock()

    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None # No tests found
    db.execute.return_value = mock_result

    with patch("backend.app.agents.validator.github_service", new_callable=AsyncMock):
        validation = await agent.validate_contribution(db, contribution, repository, client)
        assert validation.is_valid is False
        assert any(i.category == "quality" and i.severity == "high" for i in validation.issues)

@pytest.mark.asyncio
async def test_validate_contribution_security_and_process(agent):
    db = AsyncMock()
    contr_id = uuid.uuid4()
    # Diff containing suspicious file and secret finding
    contribution = Contribution(
        id=contr_id,
        branch_name="feature-x",
        diff_summary={
            "diff": "some diff",
            "files": ["src/main.py", ".env"]
        }
    )
    repository = Repository(owner="org", name="repo")
    client = MagicMock()

    # Mock DB - tests pass, but review pending
    mock_test = TestRun(status="success")
    mock_review = CodeReview(decision="REQUEST_CHANGES")

    res_test = MagicMock()
    res_test.scalars().first.return_value = mock_test
    res_review = MagicMock()
    res_review.scalars().first.return_value = mock_review
    db.execute.side_effect = [res_test, res_review]

    with patch("backend.app.agents.validator.secret_scanner") as mock_scanner, \
         patch("backend.app.agents.validator.github_service", new_callable=AsyncMock) as mock_gh:

        mock_scanner.scan_text.return_value = ["secret_found"]
        # Mock duplicate PR
        mock_gh.list_pull_requests.return_value = [
            {"head": {"ref": "feature-x"}, "title": "Existing PR"}
        ]

        validation = await agent.validate_contribution(db, contribution, repository, client)

        assert validation.is_valid is False
        # Issues expected:
        # 1. Review pending (medium)
        # 2. Secret found (critical)
        # 3. Suspicious file .env (high)
        # 4. Duplicate PR (medium)
        assert len(validation.issues) == 4

        categories = [i.category for i in validation.issues]
        assert "security" in categories
        assert "process" in categories
        assert "quality" in categories

        assert validation.score == 60 # 100 - 4*10

@pytest.mark.asyncio
async def test_validate_contribution_gh_failure(agent):
    db = AsyncMock()
    contribution = Contribution(id=uuid.uuid4(), branch_name="b", diff_summary={})
    repository = Repository(owner="o", name="n")

    # Tests and Review pass
    res = MagicMock()
    res.scalars().first.side_effect = [TestRun(status="success"), CodeReview(decision="APPROVE")]
    db.execute.return_value = res

    with patch("backend.app.agents.validator.github_service", new_callable=AsyncMock) as mock_gh:
        mock_gh.list_pull_requests.side_effect = Exception("GH Down")

        validation = await agent.validate_contribution(db, contribution, repository, MagicMock())

        # Should still be valid as GH check is in try-except
        assert validation.is_valid is True
        assert len(validation.issues) == 0
