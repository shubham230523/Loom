import pytest
from sqlalchemy import select
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from backend.app.database.models import Repository, RepositoryIndex
from backend.app.api.v1.repositories import run_discovery

@pytest.mark.asyncio
async def test_run_discovery_with_multiple_indexes(mocker, db_session):
    """Verify that run_discovery handles multiple completed index records."""
    # 1. Setup mock repo
    repo = Repository(
        github_repo_id=12345,
        owner="test",
        name="repo",
        full_name="test/repo",
        html_url="https://github.com/test/repo"
    )
    db_session.add(repo)
    await db_session.commit()
    await db_session.refresh(repo)

    # 2. Add multiple completed indexes
    idx1 = RepositoryIndex(
        repository_id=repo.id,
        branch="main",
        commit_sha="sha1",
        status="completed",
        created_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    idx2 = RepositoryIndex(
        repository_id=repo.id,
        branch="main",
        commit_sha="sha2",
        status="completed",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add_all([idx1, idx2])
    await db_session.commit()

    # 3. Mock SessionLocal and opportunity service
    mocker.patch("backend.app.api.v1.repositories.SessionLocal", return_value=db_session)
    mock_opp_service = mocker.patch("backend.app.api.v1.repositories.opportunity_service")
    mock_opp_service.discover_and_persist_opportunities = mocker.AsyncMock(return_value=0)

    # 4. Execute run_discovery (this calls the query that was failing)
    # We pass a fake token
    await run_discovery(str(repo.id), "fake_token")

    # 5. Verify it didn't crash and called the service
    mock_opp_service.discover_and_persist_opportunities.assert_called_once()
