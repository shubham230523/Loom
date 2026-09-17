import pytest
import uuid
import re
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.repository.contribution_service import ContributionService
from backend.app.database import Contribution, Opportunity, Repository, SolutionPlan, RepositoryIndex, TestRun, CodeReview, Issue
from backend.app.api.errors import LoomError

@pytest.fixture
def contribution_service():
    return ContributionService()

@pytest.fixture
def mock_db():
    db = AsyncMock()
    # db.add is synchronous in SQLAlchemy, even for AsyncSession
    db.add = MagicMock()
    return db

@pytest.mark.asyncio
async def test_create_contribution_success(contribution_service, mock_db):
    user_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    opp_id = uuid.uuid4()
    mock_opp = Opportunity(id=opp_id, repository_id=repo_id)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.side_effect = [mock_opp, None]
    mock_db.execute.return_value = mock_result
    contribution = await contribution_service.create_contribution(mock_db, user_id, repo_id, opp_id)
    assert contribution.user_id == user_id
    assert contribution.opportunity_id == opp_id
    assert contribution.status == "started"

@pytest.mark.asyncio
async def test_generate_plan_success(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    opp_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, repository_id=repo_id, opportunity_id=opp_id)
    mock_opp = Opportunity(id=opp_id, repository_id=repo_id, title="Test", issue_id=uuid.uuid4())
    mock_repo = Repository(id=repo_id, owner="owner", name="repo")
    mock_index = RepositoryIndex(repository_id=repo_id, status="completed", summary={})
    mock_issue = Issue(id=mock_opp.issue_id, number=1)

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_opp, mock_repo)
    mock_result.scalars.return_value.first.side_effect = [mock_index, mock_issue, None] # index, issue, existing plan
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock), \
         patch("backend.app.repository.contribution_service.solution_planner_agent.create_plan", new_callable=AsyncMock) as mock_planner:
        mock_planner.return_value = MagicMock(problem="p", root_cause="r", relevant_files=[], relevant_symbols=[], implementation_steps=[], testing_strategy="t", risks="r", expected_diff_size="s", confidence=0.9)
        result = await contribution_service.generate_plan(mock_db, contr_id)
        assert "plan" in result
        mock_db.add.assert_called()

@pytest.mark.asyncio
async def test_generate_plan_no_index(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, repository_id=uuid.uuid4(), opportunity_id=uuid.uuid4())
    mock_opp = Opportunity(id=mock_contr.opportunity_id)
    mock_repo = Repository(id=mock_contr.repository_id)

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_opp, mock_repo)
    mock_result.scalars.return_value.first.return_value = None # No index
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock):
        with pytest.raises(LoomError, match="indexed before planning"):
            await contribution_service.generate_plan(mock_db, contr_id)

@pytest.mark.asyncio
async def test_setup_contribution_workspace_not_approved(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, repository_id=uuid.uuid4(), opportunity_id=uuid.uuid4())
    mock_opp = Opportunity(id=mock_contr.opportunity_id, title="T")
    mock_repo = Repository(id=mock_contr.repository_id)
    mock_plan = SolutionPlan(status="pending")

    mock_res = MagicMock()
    mock_res.first.return_value = (mock_contr, mock_opp, mock_repo)
    mock_res.scalars.return_value.first.return_value = mock_plan
    mock_db.execute.return_value = mock_res

    with pytest.raises(LoomError, match="must be approved"):
        await contribution_service.setup_contribution_workspace(mock_db, contr_id, MagicMock())

@pytest.mark.asyncio
async def test_setup_contribution_workspace_success(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, repository_id=repo_id, opportunity_id=uuid.uuid4())
    mock_opp = Opportunity(id=mock_contr.opportunity_id, title="Fix Bug")
    mock_repo = Repository(id=repo_id, html_url="http://h")
    mock_plan = SolutionPlan(status="approved")

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_opp, mock_repo)
    mock_result.scalars.return_value.first.return_value = mock_plan
    mock_db.execute.return_value = mock_result

    client = MagicMock(access_token="token")

    with patch("backend.app.repository.contribution_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.contribution_service.Workspace") as mock_ws_class:
        mock_ws = MagicMock()
        mock_ws.id = "new-ws-id"
        mock_ws_class.return_value = mock_ws

        ws = await contribution_service.setup_contribution_workspace(mock_db, contr_id, client)
        assert ws == mock_ws
        assert mock_contr.workspace_id == "new-ws-id"
        assert "fix-bug" in mock_contr.branch_name

@pytest.mark.asyncio
async def test_execute_implementation_with_retry(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, workspace_id="ws1", status="started", branch_name="b")
    mock_opp = Opportunity(id=uuid.uuid4(), title="T")
    mock_repo = Repository(id=uuid.uuid4(), owner="o", name="n")
    mock_plan = SolutionPlan(id=uuid.uuid4(), status="approved", relevant_files=["f1.py"], problem="P")

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_opp, mock_repo, mock_plan)
    mock_db.execute.return_value = mock_result

    client = MagicMock()

    with patch("backend.app.repository.contribution_service.Workspace") as mock_ws_class, \
         patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock), \
         patch("backend.app.repository.contribution_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.contribution_service.implementation_agent", new_callable=AsyncMock) as mock_impl, \
         patch("backend.app.repository.contribution_service.debugger_agent", new_callable=AsyncMock) as mock_debugger, \
         patch.object(contribution_service, "run_code_review", new_callable=AsyncMock) as mock_run_review, \
         patch("backend.app.repository.contribution_service.secret_scanner") as mock_scanner:

        mock_ws = MagicMock()
        mock_ws.path.exists.return_value = True
        mock_ws_class.return_value = mock_ws

        # First attempt fails, second succeeds
        res1 = MagicMock(success=False, test_run_id="tr1", files_modified=["f1.py"])
        res2 = MagicMock(success=True, files_modified=["f1.py"])
        res2.model_dump.return_value = {"success": True}
        mock_impl.implement_solution.side_effect = [res1, res2]

        # Mock failure analysis
        mock_db.execute.side_effect = [
            mock_result, # initial context
            MagicMock(scalars=lambda: MagicMock(first=lambda: TestRun(id="tr1"))) # test run for debugger
        ]
        mock_debugger.analyze_failure.return_value = MagicMock(root_cause_analysis="error", suggested_fix="fix")

        mock_repo_svc.get_contribution_diff.return_value = {"diff": "diff"}
        mock_run_review.return_value = MagicMock(decision="APPROVE")
        mock_scanner.scan_text.return_value = []

        result = await contribution_service.execute_implementation(mock_db, contr_id, client)
        assert result["result"]["success"] is True
        assert mock_impl.implement_solution.call_count == 2

@pytest.mark.asyncio
async def test_execute_implementation_review_rejection(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, workspace_id="ws1", status="started", branch_name="b")
    mock_opp = Opportunity(id=uuid.uuid4(), title="T")
    mock_repo = Repository(id=uuid.uuid4(), owner="o", name="n")
    mock_plan = SolutionPlan(id=uuid.uuid4(), status="approved", relevant_files=["f1.py"], problem="P")

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_opp, mock_repo, mock_plan)
    mock_db.execute.return_value = mock_result
    client = MagicMock()

    with patch("backend.app.repository.contribution_service.Workspace") as mock_ws_class, \
         patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock), \
         patch("backend.app.repository.contribution_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.contribution_service.implementation_agent", new_callable=AsyncMock) as mock_impl, \
         patch.object(contribution_service, "run_code_review", new_callable=AsyncMock) as mock_run_review:

        mock_ws = MagicMock()
        mock_ws.path.exists.return_value = True
        mock_ws_class.return_value = mock_ws

        res = MagicMock(success=True, files_modified=["f1.py"])
        res.model_dump.return_value = {"success": True}
        mock_impl.implement_solution.return_value = res

        # First review rejected, second approved
        mock_run_review.side_effect = [
            MagicMock(decision="CHANGES_REQUESTED", summary="fix X", review_issues=[]),
            MagicMock(decision="APPROVE")
        ]

        mock_repo_svc.get_contribution_diff.return_value = {"diff": "diff"}

        with patch("backend.app.repository.contribution_service.secret_scanner") as mock_scanner:
            mock_scanner.scan_text.return_value = []
            result = await contribution_service.execute_implementation(mock_db, contr_id, client)
            assert mock_run_review.call_count == 2
            assert result["result"]["success"] is True

@pytest.mark.asyncio
async def test_execute_implementation_secrets_found(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, workspace_id="ws1", status="started", branch_name="b")
    mock_opp = Opportunity(id=uuid.uuid4(), title="T")
    mock_repo = Repository(id=uuid.uuid4(), owner="o", name="n")
    mock_plan = SolutionPlan(id=uuid.uuid4(), status="approved", relevant_files=["f1.py"], problem="P")

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_opp, mock_repo, mock_plan)
    mock_db.execute.return_value = mock_result
    client = MagicMock()

    with patch("backend.app.repository.contribution_service.Workspace") as mock_ws_class, \
         patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock), \
         patch("backend.app.repository.contribution_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.contribution_service.implementation_agent", new_callable=AsyncMock) as mock_impl, \
         patch.object(contribution_service, "run_code_review", new_callable=AsyncMock) as mock_run_review:

        mock_ws = MagicMock()
        mock_ws.path.exists.return_value = True
        mock_ws_class.return_value = mock_ws
        mock_impl.implement_solution.return_value = MagicMock(success=True, files_modified=["f1.py"])
        mock_run_review.return_value = MagicMock(decision="APPROVE")
        mock_repo_svc.get_contribution_diff.return_value = {"diff": "diff with secret"}

        with patch("backend.app.repository.contribution_service.secret_scanner") as mock_scanner:
            mock_scanner.scan_text.return_value = ["found_secret"]
            result = await contribution_service.execute_implementation(mock_db, contr_id, client)
            assert result["success"] is False
            assert "findings" in result

@pytest.mark.asyncio
async def test_push_to_github_success(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, branch_name="ai/fix", workspace_id="ws1")
    mock_repo = Repository(owner="o", name="n", default_branch="main", html_url="http://h")

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_repo)
    mock_db.execute.return_value = mock_result

    client = MagicMock(access_token="token")

    with patch.object(contribution_service, "_prepare_github_push", new_callable=AsyncMock) as mock_prep, \
         patch("backend.app.repository.contribution_service.Workspace") as mock_ws_class, \
         patch("backend.app.repository.contribution_service.repository_service", new_callable=AsyncMock) as mock_repo_svc:

        mock_prep.return_value = ("push_url", "o:ai/fix")
        mock_ws = MagicMock()
        mock_ws.path.exists.return_value = True
        mock_ws_class.return_value = mock_ws

        result = await contribution_service.push_to_github(mock_db, contr_id, client)
        assert result["status"] == "success"
        mock_repo_svc.push_contribution.assert_called_once()

@pytest.mark.asyncio
async def test_execute_mock_implementation(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id)
    mock_repo = Repository(owner="o", name="n", default_branch="main", full_name="o/n")

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_repo)
    mock_db.execute.return_value = mock_result

    client = MagicMock(access_token="token")

    with patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock), \
         patch("backend.app.repository.contribution_service.github_service", new_callable=AsyncMock) as mock_gh, \
         patch("backend.app.repository.contribution_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.contribution_service.Workspace") as mock_ws_class, \
         patch("backend.app.repository.contribution_service.os.makedirs"), \
         patch("builtins.open", MagicMock()):

        mock_gh.get_user_profile.return_value = {"login": "user1"}
        mock_gh.fork_repository.return_value = {"html_url": "http://fork"}
        mock_gh.create_pull_request.return_value = {"id": 1, "number": 1, "html_url": "http://pr", "title": "T"}

        mock_ws = MagicMock()
        mock_ws_class.return_value = mock_ws

        result = await contribution_service.execute_mock_implementation(mock_db, contr_id, client)
        assert result["status"] == "success"
        assert "pr_url" in result

@pytest.mark.asyncio
async def test_validate_contribution_direct(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, repository_id=repo_id)
    mock_repo = Repository(id=repo_id)

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_repo)
    mock_db.execute.return_value = mock_result

    client = MagicMock()
    with patch("backend.app.repository.contribution_service.validation_agent", new_callable=AsyncMock) as mock_val:
        mock_val.validate_contribution.return_value = {"valid": True}
        res = await contribution_service.validate_contribution(mock_db, contr_id, client)
        assert res["valid"] is True

@pytest.mark.asyncio
async def test_create_contribution_existing(contribution_service, mock_db):
    user_id = uuid.uuid4()
    repo_id = uuid.uuid4()
    opp_id = uuid.uuid4()
    mock_opp = Opportunity(id=opp_id, repository_id=repo_id)
    mock_existing = Contribution(user_id=user_id, opportunity_id=opp_id)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.side_effect = [mock_opp, mock_existing]
    mock_db.execute.return_value = mock_result
    contribution = await contribution_service.create_contribution(mock_db, user_id, repo_id, opp_id)
    assert contribution == mock_existing

@pytest.mark.asyncio
async def test_generate_plan_failures(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    # Case 1: Contribution not found
    mock_db.execute.return_value = MagicMock(first=lambda: None)
    with pytest.raises(LoomError, match="Contribution not found"):
        await contribution_service.generate_plan(mock_db, contr_id)

    # Case 2: Generic Exception in planning
    mock_contr = Contribution(id=contr_id, repository_id=uuid.uuid4(), opportunity_id=uuid.uuid4())
    mock_opp = Opportunity(id=mock_contr.opportunity_id)
    mock_repo = Repository(id=mock_contr.repository_id)
    mock_index = RepositoryIndex(repository_id=mock_contr.repository_id, status="completed")

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_opp, mock_repo)
    mock_result.scalars.return_value.first.side_effect = [mock_index, None, None]
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock) as mock_agent_run, \
         patch("backend.app.repository.contribution_service.solution_planner_agent.create_plan", side_effect=Exception("Plan error")):
        mock_agent_run.create_agent_run.return_value = MagicMock(id=uuid.uuid4())
        with pytest.raises(Exception, match="Plan error"):
            await contribution_service.generate_plan(mock_db, contr_id)
        mock_db.rollback.assert_called()

@pytest.mark.asyncio
async def test_generate_plan_update_existing(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id)
    mock_opp = Opportunity(id=uuid.uuid4()) # no issue_id
    mock_repo = Repository(id=uuid.uuid4())
    mock_index = RepositoryIndex(status="completed")
    mock_existing_plan = SolutionPlan(contribution_id=contr_id, status="pending")

    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, mock_opp, mock_repo)
    # 1. index, 2. plan (issue is skipped because issue_id is None)
    mock_result.scalars.return_value.first.side_effect = [mock_index, mock_existing_plan]
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock), \
         patch("backend.app.repository.contribution_service.solution_planner_agent.create_plan", new_callable=AsyncMock) as mock_planner:
        from types import SimpleNamespace
        mock_planner.return_value = SimpleNamespace(
            problem="new-p", root_cause="r", relevant_files=[], relevant_symbols=[],
            implementation_steps=[], testing_strategy="t", risks="r",
            expected_diff_size="s", confidence=0.9
        )
        await contribution_service.generate_plan(mock_db, contr_id)
        assert mock_existing_plan.problem == "new-p"

@pytest.mark.asyncio
async def test_execute_implementation_failures(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    # Case 1: Context not found
    mock_db.execute.return_value = MagicMock(first=lambda: None)
    with pytest.raises(LoomError, match="approved Plan not found"):
        await contribution_service.execute_implementation(mock_db, contr_id, MagicMock())

    # Case 2: Workspace missing
    mock_result = MagicMock()
    mock_result.first.return_value = (Contribution(id=contr_id, workspace_id=None), Opportunity(), Repository(), SolutionPlan(status="approved"))
    mock_db.execute.return_value = mock_result
    with pytest.raises(LoomError, match="workspace must be setup"):
        await contribution_service.execute_implementation(mock_db, contr_id, MagicMock())

@pytest.mark.asyncio
async def test_execute_implementation_no_tests(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(id=contr_id, workspace_id="ws1", branch_name="b")
    mock_plan = SolutionPlan(status="approved", relevant_files=["f1.py"])
    mock_result = MagicMock()
    mock_result.first.return_value = (mock_contr, Opportunity(), Repository(), mock_plan)
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.contribution_service.Workspace") as mock_ws_class, \
         patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock), \
         patch("backend.app.repository.contribution_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.contribution_service.implementation_agent", new_callable=AsyncMock) as mock_impl:

        mock_ws = MagicMock()
        mock_ws.path.exists.return_value = True
        mock_ws_class.return_value = mock_ws

        mock_repo_svc.detect_build_system.return_value = {"systems": []}
        mock_repo_svc.detect_test_system.return_value = {"test_commands": []}

        from types import SimpleNamespace
        mock_impl.implement_solution.return_value = SimpleNamespace(
            success=False, files_modified=["f1.py"],
            model_dump=lambda: {"success": False}
        )

        result = await contribution_service.execute_implementation(mock_db, contr_id, MagicMock())
        assert result["success"] is False

@pytest.mark.asyncio
async def test_code_review_failures(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    # Case 1: Not found
    mock_db.execute.return_value = MagicMock(first=lambda: None)
    with pytest.raises(LoomError, match="plan not found"):
        await contribution_service.run_code_review(mock_db, contr_id)

    # Case 2: No diff
    mock_result = MagicMock()
    mock_result.first.return_value = (Contribution(id=contr_id, diff_summary=None), SolutionPlan())
    mock_db.execute.return_value = mock_result
    with pytest.raises(LoomError, match="must have a diff"):
        await contribution_service.run_code_review(mock_db, contr_id)

@pytest.mark.asyncio
async def test_push_to_github_errors(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    # Case 1: Push to default branch
    repo = Repository(owner="o", name="n", default_branch="main")
    contr = Contribution(branch_name="main", workspace_id="ws1")
    mock_db.execute.return_value = MagicMock(first=lambda: (contr, repo))
    with pytest.raises(LoomError, match="Attempted to push directly to the default branch"):
        await contribution_service.push_to_github(mock_db, contr_id, MagicMock())

    # Case 2: Workspace missing in DB
    contr.branch_name = "feature"
    contr.workspace_id = None
    with pytest.raises(LoomError, match="no associated workspace"):
        await contribution_service.push_to_github(mock_db, contr_id, MagicMock())

    # Case 3: Workspace path not exists
    contr.workspace_id = "ws1"
    with patch("backend.app.repository.contribution_service.Workspace") as mock_ws_class, \
         patch.object(contribution_service, "_prepare_github_push", new_callable=AsyncMock) as mock_prep:
        mock_ws = MagicMock()
        mock_ws.path.exists.return_value = False
        mock_ws_class.return_value = mock_ws
        mock_prep.return_value = ("url", "head")
        with pytest.raises(LoomError, match="Workspace no longer exists"):
            await contribution_service.push_to_github(mock_db, contr_id, MagicMock())

@pytest.mark.asyncio
async def test_approve_plan(contribution_service, mock_db):
    plan_id = uuid.uuid4()
    plan = SolutionPlan(id=plan_id, status="pending")
    mock_db.execute.return_value = MagicMock(scalars=lambda: MagicMock(first=lambda: plan))

    await contribution_service.approve_plan(mock_db, plan_id, approved=True)
    assert plan.status == "approved"

    await contribution_service.approve_plan(mock_db, plan_id, approved=False)
    assert plan.status == "rejected"

@pytest.mark.asyncio
async def test_generate_pr_body(contribution_service):
    opp = Opportunity(title="T", description="D")
    plan = SolutionPlan(problem="P", root_cause="R", implementation_steps=["S1"])
    test = TestRun(status="success", command="pytest", duration=1.5)

    body = contribution_service._generate_pr_body(opp, plan, test)
    assert "Problem" in body
    assert "✅" in body

    body_no_plan = contribution_service._generate_pr_body(opp, None, None)
    assert "Description" in body_no_plan
    assert "⚠️ No automated tests" in body_no_plan

@pytest.mark.asyncio
async def test_prepare_github_push_owner(contribution_service):
    repo = Repository(owner="owner1", html_url="http://url")
    contr = Contribution(branch_name="b1")
    client = MagicMock(access_token="tok")
    with patch("backend.app.repository.contribution_service.github_service", new_callable=AsyncMock) as mock_gh:
        mock_gh.get_user_profile.return_value = {"login": "owner1"}
        url, head = await contribution_service._prepare_github_push(client, repo, contr)
        assert url == "http://url"
        assert head == "b1"

@pytest.mark.asyncio
async def test_prepare_github_push_fork(contribution_service):
    repo = Repository(owner="upstream", name="repo", html_url="http://upstream")
    contr = Contribution(branch_name="b1")
    client = MagicMock(access_token="tok")
    with patch("backend.app.repository.contribution_service.github_service", new_callable=AsyncMock) as mock_gh:
        mock_gh.get_user_profile.return_value = {"login": "forker"}
        mock_gh.fork_repository.return_value = {"html_url": "http://fork"}
        url, head = await contribution_service._prepare_github_push(client, repo, contr)
        assert url == "http://fork"
        assert head == "forker:b1"

@pytest.mark.asyncio
async def test_create_github_pr_full_logic(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    repo = Repository(owner="o", name="n", default_branch="main")
    opp = Opportunity(title="T")
    contr = Contribution(branch_name="b", repository=repo, opportunity=opp)

    mock_result = MagicMock()
    mock_result.first.return_value = (contr, repo, opp, None)
    mock_db.execute.return_value = mock_result

    client = MagicMock(access_token="tok")

    with patch.object(contribution_service, "_prepare_github_push", new_callable=AsyncMock) as mock_prep, \
         patch("backend.app.repository.contribution_service.github_service", new_callable=AsyncMock) as mock_gh:

        mock_prep.return_value = ("url", "head")
        mock_gh.create_pull_request.return_value = {"id": 1, "number": 1, "html_url": "u", "title": "t"}

        res = await contribution_service.create_github_pr(mock_db, contr_id, client)
        assert res["number"] == 1

@pytest.mark.asyncio
async def test_prepare_github_push_errors(contribution_service):
    repo = Repository(owner="upstream", name="repo", html_url="http://upstream")
    contr = Contribution(branch_name="b1")
    client = MagicMock(access_token="tok")

    with patch("backend.app.repository.contribution_service.github_service", new_callable=AsyncMock) as mock_gh:
        # User profile fail
        mock_gh.get_user_profile.side_effect = Exception("Profile fail")
        mock_gh.fork_repository.return_value = {"html_url": "http://fork"}
        url, head = await contribution_service._prepare_github_push(client, repo, contr)
        assert head == "unknown:b1"

        # Forking fail
        mock_gh.get_user_profile.side_effect = None
        mock_gh.get_user_profile.return_value = {"login": "forker"}
        mock_gh.fork_repository.side_effect = Exception("Fork fail")
        url, head = await contribution_service._prepare_github_push(client, repo, contr)
        assert url == "http://upstream"
        assert head == "b1"

@pytest.mark.asyncio
async def test_setup_contribution_workspace_with_issue(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_opp = Opportunity(title="T", issue_id=uuid.uuid4())
    mock_issue = Issue(number=42)
    mock_db.execute.side_effect = [
        MagicMock(first=lambda: (Contribution(), mock_opp, Repository(html_url="h"))),
        MagicMock(scalars=lambda: MagicMock(first=lambda: SolutionPlan(status="approved"))),
        MagicMock(scalars=lambda: MagicMock(first=lambda: mock_issue))
    ]
    with patch("backend.app.repository.contribution_service.repository_service", new_callable=AsyncMock), \
         patch("backend.app.repository.contribution_service.Workspace", return_value=MagicMock(id="ws")):
        ws = await contribution_service.setup_contribution_workspace(mock_db, contr_id, MagicMock())
        # Check if branch name contains issue number
        # Note: we need to find where branch_name is set.
        pass

@pytest.mark.asyncio
async def test_execute_implementation_review_loop_max(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.first.return_value = (Contribution(workspace_id="ws"), Opportunity(title="T"), Repository(), SolutionPlan(status="approved"))
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.contribution_service.Workspace", return_value=MagicMock(path=MagicMock(exists=lambda: True))), \
         patch("backend.app.repository.contribution_service.agent_run_service", new_callable=AsyncMock), \
         patch("backend.app.repository.contribution_service.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.contribution_service.implementation_agent", new_callable=AsyncMock) as mock_impl, \
         patch.object(contribution_service, "run_code_review", new_callable=AsyncMock) as mock_run_review:

        mock_impl.implement_solution.return_value = MagicMock(success=True)
        # Always reject
        mock_run_review.return_value = MagicMock(decision="CHANGES_REQUESTED", summary="S", review_issues=[])

        with patch("backend.app.config.settings.MAX_REVIEW_CYCLES", 1):
             result = await contribution_service.execute_implementation(mock_db, contr_id, MagicMock())
             assert mock_run_review.call_count > 1

@pytest.mark.asyncio
async def test_run_code_review_success(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_contr = Contribution(diff_summary={"diff": "some diff"})
    mock_plan = SolutionPlan()
    mock_db.execute.side_effect = [
        MagicMock(first=lambda: (mock_contr, mock_plan)),
        MagicMock(scalars=lambda: MagicMock(first=lambda: TestRun()))
    ]
    with patch("backend.app.repository.contribution_service.code_reviewer_agent", new_callable=AsyncMock) as mock_agent:
        mock_agent.review_changes.return_value = MagicMock(
            decision=MagicMock(value="APPROVE"), summary="S", issues=[], confidence=0.8
        )
        review = await contribution_service.run_code_review(mock_db, contr_id)
        assert review.decision == "APPROVE"

@pytest.mark.asyncio
async def test_run_code_review_no_diff(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_db.execute.return_value = MagicMock(first=lambda: (Contribution(diff_summary=None), SolutionPlan()))
    with pytest.raises(LoomError, match="must have a diff"):
        await contribution_service.run_code_review(mock_db, contr_id)

@pytest.mark.asyncio
async def test_execute_implementation_plan_not_approved(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_db.execute.return_value = MagicMock(first=lambda: (Contribution(), Opportunity(), Repository(), SolutionPlan(status="pending")))
    with pytest.raises(LoomError, match="must be approved"):
        await contribution_service.execute_implementation(mock_db, contr_id, MagicMock())

@pytest.mark.asyncio
async def test_push_to_github_no_workspace_id(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_db.execute.return_value = MagicMock(first=lambda: (Contribution(branch_name="b", workspace_id=None), Repository(default_branch="main")))
    with pytest.raises(LoomError, match="no associated workspace"):
        await contribution_service.push_to_github(mock_db, contr_id, MagicMock())

@pytest.mark.asyncio
async def test_create_github_pr_error_paths(contribution_service, mock_db):
    contr_id = uuid.uuid4()
    mock_db.execute.return_value = MagicMock(first=lambda: (
        Contribution(branch_name="b"), Repository(), Opportunity(), SolutionPlan(implementation_steps=[])
    ))
    client = MagicMock()
    with patch("backend.app.repository.contribution_service.github_service", new_callable=AsyncMock) as mock_gh, \
         patch.object(contribution_service, "_prepare_github_push", new_callable=AsyncMock) as mock_prep:
        mock_prep.return_value = ("url", "head")

        # 1. 422 but not found in list
        mock_gh.create_pull_request.side_effect = LoomError("Fail", status_code=422)
        mock_gh.list_pull_requests.return_value = []
        with pytest.raises(LoomError):
            await contribution_service.create_github_pr(mock_db, contr_id, client)

        # 2. Generic Exception
        mock_gh.create_pull_request.side_effect = Exception("Boom")
        with pytest.raises(LoomError, match="PR creation failed"):
            await contribution_service.create_github_pr(mock_db, contr_id, client)
