import pytest
import uuid
import time
from unittest.mock import AsyncMock, patch
from backend.app.services.agent_run_service import AgentRunService
from backend.app.database.models import AgentRun, User, Repository, Opportunity, Contribution

@pytest.fixture
def service():
    return AgentRunService()

async def create_test_contribution(db_session):
    import random
    unique_id = random.randint(1, 1000000000)
    user = User(username=f"u_{uuid.uuid4()}", github_user_id=unique_id)
    repo = Repository(github_repo_id=unique_id, owner="o", name="n", full_name=f"o/n_{uuid.uuid4()}", html_url="h")
    db_session.add(user)
    db_session.add(repo)
    await db_session.flush()

    opp = Opportunity(repository_id=repo.id, title="T", description="D", type="bug", impact="high", difficulty="easy")
    db_session.add(opp)
    await db_session.flush()

    contr = Contribution(user_id=user.id, repository_id=repo.id, opportunity_id=opp.id)
    db_session.add(contr)
    await db_session.commit()
    return contr

@pytest.mark.asyncio
async def test_create_agent_run(service, db_session):
    contr = await create_test_contribution(db_session)
    contr_id = contr.id
    with patch("backend.app.services.agent_run_service.agent_broadcaster", new_callable=AsyncMock):
        run = await service.create_agent_run(db_session, contr_id, "coder")
        assert run.agent_type == "coder"
        assert run.status == "running"

@pytest.mark.asyncio
async def test_complete_run_success(service, db_session):
    contr = await create_test_contribution(db_session)
    contr_id = contr.id
    run = AgentRun(contribution_id=contr_id, agent_type="coder", status="running")
    db_session.add(run)
    await db_session.commit()
    await db_session.refresh(run)

    run_id = run.id

    with patch("backend.app.services.agent_run_service.agent_broadcaster", new_callable=AsyncMock):
        await service.complete_run(db_session, run_id, success=True)

        await db_session.refresh(run)
        assert run.status == "completed"
        assert run.completed_at is not None

@pytest.mark.asyncio
async def test_emit_event_failures(service, db_session):
    run_id = uuid.uuid4()
    # 1. DB persistence failure
    with patch.object(db_session, "add", side_effect=Exception("DB Fail")), \
         patch("backend.app.services.agent_run_service.agent_broadcaster", new_callable=AsyncMock) as mock_broadcaster:
        await service.emit_event(db_session, run_id, "ev", "msg")
        # Should still broadcast
        mock_broadcaster.broadcast.assert_called_once()

    # 2. Broadcast failure
    with patch("backend.app.services.agent_run_service.agent_broadcaster.broadcast", side_effect=Exception("WS Fail")):
        # Should not raise
        await service.emit_event(db_session, run_id, "ev", "msg")

@pytest.mark.asyncio
async def test_complete_run_not_found(service, db_session):
    run_id = uuid.uuid4()
    with patch("backend.app.services.agent_run_service.agent_broadcaster", new_callable=AsyncMock):
        # Should not raise
        await service.complete_run(db_session, run_id, success=False)

@pytest.mark.asyncio
async def test_complete_run_db_error(service, db_session):
    run_id = uuid.uuid4()
    with patch.object(db_session, "execute", side_effect=Exception("DB Fail")), \
         patch("backend.app.services.agent_run_service.agent_broadcaster", new_callable=AsyncMock):
        # Should not raise
        await service.complete_run(db_session, run_id, success=True)
