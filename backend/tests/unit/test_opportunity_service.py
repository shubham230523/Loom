import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.repository.opportunity_service import OpportunityService
from backend.app.database import Repository, RepositoryIndex, Opportunity, Issue
import uuid

@pytest.fixture
def opp_service():
    return OpportunityService()

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    return db

@pytest.mark.asyncio
async def test_discover_and_persist_opportunities_success(opp_service, mock_db):
    repo = Repository(id=uuid.uuid4(), owner="o", name="n")
    client = AsyncMock()
    index = RepositoryIndex(id="idx", status="completed", summary={})

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = index
    mock_result.scalars.return_value.all.return_value = [] # No existing issues
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.opportunity_service.Workspace", return_value=AsyncMock()), \
         patch("backend.app.repository.opportunity_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.opportunity_service.pr_service", new_callable=AsyncMock) as mock_pr_svc, \
         patch("backend.app.repository.opportunity_service.opportunity_generator_agent", new_callable=AsyncMock) as mock_agent:

        mock_repo_svc.detect_code_signals.return_value = []
        mock_repo_svc.discover_files.return_value = []
        mock_repo_svc.detect_test_gaps.return_value = []
        mock_pr_svc.get_repository_pull_requests.return_value = []

        mock_proposal = MagicMock(title="T", description="D", type="bug", impact="H", difficulty="E", confidence=0.9)
        mock_agent.generate_opportunities.return_value = [mock_proposal]

        count = await opp_service.discover_and_persist_opportunities(mock_db, repo, client)

        assert count == 1
        assert repo.discovery_status == "completed"
        mock_db.commit.assert_called()

@pytest.mark.asyncio
async def test_discover_and_persist_opportunities_no_index(opp_service, mock_db):
    repo = Repository(id=uuid.uuid4())
    client = AsyncMock()
    mock_db.execute.return_value = MagicMock(scalars=lambda: MagicMock(first=lambda: None))

    res = await opp_service.discover_and_persist_opportunities(mock_db, repo, client)
    assert res == 0
    assert repo.discovery_status == "failed"

@pytest.mark.asyncio
async def test_discover_and_persist_opportunities_agent_error_no_signals(opp_service, mock_db):
    repo = Repository(id=uuid.uuid4())
    client = AsyncMock()
    index = RepositoryIndex(id="idx", status="completed")

    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = index
    mock_res.scalars.return_value.all.return_value = [] # issues
    mock_db.execute.return_value = mock_res

    with patch("backend.app.repository.opportunity_service.Workspace", return_value=AsyncMock()), \
         patch("backend.app.repository.opportunity_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.opportunity_service.pr_service", new_callable=AsyncMock) as mock_pr_svc, \
         patch("backend.app.repository.opportunity_service.opportunity_generator_agent", new_callable=AsyncMock) as mock_agent:

        mock_repo_svc.detect_code_signals.return_value = []
        mock_repo_svc.detect_test_gaps.return_value = []
        mock_pr_svc.get_repository_pull_requests.return_value = []
        mock_agent.generate_opportunities.side_effect = Exception("AI Fail")

        res = await opp_service.discover_and_persist_opportunities(mock_db, repo, client)
        assert res == 0
        assert repo.discovery_status == "completed"

@pytest.mark.asyncio
async def test_discover_and_persist_opportunities_fallback(opp_service, mock_db):
    repo = Repository(id=uuid.uuid4())
    client = AsyncMock()
    index = RepositoryIndex(id="idx", status="completed")

    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = index
    mock_res.scalars.return_value.all.return_value = [Issue(number=1, title="I", labels=["bug"])]
    mock_db.execute.return_value = mock_res

    with patch("backend.app.repository.opportunity_service.Workspace", return_value=AsyncMock()), \
         patch("backend.app.repository.opportunity_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.opportunity_service.pr_service", new_callable=AsyncMock) as mock_pr_svc, \
         patch("backend.app.repository.opportunity_service.opportunity_generator_agent", new_callable=AsyncMock) as mock_agent:

        mock_repo_svc.detect_code_signals.return_value = [{"path": "f.py", "line": 1, "content": "TODO"}]
        mock_repo_svc.detect_test_gaps.return_value = []
        mock_pr_svc.get_repository_pull_requests.return_value = []
        mock_agent.generate_opportunities.side_effect = Exception("AI Fail")

        res = await opp_service.discover_and_persist_opportunities(mock_db, repo, client)
        assert res > 0
        assert repo.discovery_status == "completed"

@pytest.mark.asyncio
async def test_score_opportunity_success(opp_service, mock_db):
    opp_id = uuid.uuid4()
    repo = Repository(id=uuid.uuid4(), owner="o", name="n")
    index = RepositoryIndex(id="idx", summary={})
    client = AsyncMock()

    opportunity = Opportunity(id=opp_id, title="T", description="D", type="bug")

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = opportunity
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.opportunity_service.pr_service", new_callable=AsyncMock) as mock_pr_svc, \
         patch("backend.app.repository.opportunity_service.scoring_agent", new_callable=AsyncMock) as mock_score_agent:

        mock_pr_svc.get_repository_pull_requests.return_value = [{"state": "open"}]
        mock_score_agent.score_opportunity.return_value = MagicMock(overall_score=88, model_dump=lambda: {"r": "reason"})

        updated_opp = await opp_service.score_opportunity(mock_db, opp_id, repo, index, client)

        assert updated_opp.score == 88.0
        mock_db.commit.assert_called()

@pytest.mark.asyncio
async def test_score_opportunity_not_found(opp_service, mock_db):
    mock_db.execute.return_value = MagicMock(scalars=lambda: MagicMock(first=lambda: None))
    res = await opp_service.score_opportunity(mock_db, uuid.uuid4(), MagicMock(), MagicMock(), MagicMock())
    assert res is None

@pytest.mark.asyncio
async def test_list_and_details(opp_service, mock_db):
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = [Opportunity(title="O1")]
    mock_res.scalars.return_value.first.return_value = Opportunity(title="O2")
    mock_db.execute.return_value = mock_res

    l = await opp_service.list_opportunities(mock_db, uuid.uuid4())
    assert len(l) == 1

    d = await opp_service.get_opportunity_details(mock_db, uuid.uuid4())
    assert d.title == "O2"
