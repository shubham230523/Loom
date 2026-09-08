import pytest
from uuid import uuid4
from unittest.mock import AsyncMock
from backend.app.repository.contribution_service import ContributionService
from backend.app.database.models import User, Contribution, Repository, RepositoryIndex, SolutionPlan, Opportunity
from backend.app.api.errors import LoomError

@pytest.mark.asyncio
async def test_generate_plan_requires_index(db_session, mocker):
    """Verify that planning fails if the repository is not indexed."""
    # 1. Setup user, repo and contribution
    user = User(id=uuid4(), github_user_id=1, username="test")
    repo = Repository(
        id=uuid4(),
        github_repo_id=1,
        owner="org",
        name="repo",
        full_name="org/repo",
        html_url="http://gh"
    )
    opp = Opportunity(
        id=uuid4(),
        repository_id=repo.id,
        title="Bug",
        description="Fix",
        type="bug",
        impact="high",
        difficulty="medium"
    )
    contrib = Contribution(
        id=uuid4(),
        user_id=user.id,
        repository_id=repo.id,
        opportunity_id=opp.id,
        status="started"
    )

    db_session.add_all([user, repo, opp, contrib])
    await db_session.commit()

    # Mock index search to return None
    service = ContributionService()

    with pytest.raises(LoomError) as exc:
        await service.generate_plan(db_session, contrib.id)

    assert "indexed before planning" in str(exc.value)

@pytest.mark.asyncio
async def test_execute_implementation_requires_approval(db_session, mocker):
    """Verify that implementation cannot start without an approved plan."""
    # 1. Setup
    user = User(id=uuid4(), github_user_id=2, username="test2")
    repo = Repository(
        id=uuid4(),
        github_repo_id=2,
        owner="org2",
        name="repo2",
        full_name="org2/repo2",
        html_url="http://gh2"
    )
    opp = Opportunity(
        id=uuid4(),
        repository_id=repo.id,
        title="Bug",
        description="Fix",
        type="bug",
        impact="high",
        difficulty="medium"
    )
    contrib = Contribution(
        id=uuid4(),
        user_id=user.id,
        repository_id=repo.id,
        opportunity_id=opp.id,
        status="started"
    )
    plan = SolutionPlan(
        id=uuid4(),
        contribution_id=contrib.id,
        status="pending",
        problem="X",
        root_cause="Y",
        implementation_steps=[],
        relevant_files=[],
        relevant_symbols=[],
        testing_strategy="Z",
        risks="None",
        expected_diff_size="Small",
        confidence=1.0
    )

    db_session.add_all([user, repo, opp, contrib, plan])
    await db_session.commit()

    service = ContributionService()

    with pytest.raises(LoomError) as exc:
        await service.execute_implementation(db_session, contrib.id, mocker.Mock())

    assert "must be approved" in str(exc.value)
