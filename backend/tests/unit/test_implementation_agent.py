import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.agents.implementation import ImplementationAgent, FileChange, ImplementationResult
from backend.app.database.models import Repository, SolutionPlan, Contribution, TestRun
from backend.app.ai.schemas import ChatResponse, ChatMessage, MessageRole

@pytest.fixture
def agent():
    return ImplementationAgent()

@pytest.fixture
def mock_db():
    return AsyncMock()

@pytest.fixture
def mock_repo():
    return Repository(id="repo1", full_name="org/repo")

@pytest.fixture
def mock_plan():
    return SolutionPlan(
        id="plan1",
        problem="Fix bug",
        implementation_steps=["Step 1", "Step 2"],
        relevant_files=["file1.py", "file2.py"]
    )

@pytest.fixture
def mock_contribution():
    return Contribution(id="contrib1")

@pytest.mark.asyncio
async def test_implement_solution_success(agent, mock_db, mock_repo, mock_plan, mock_contribution, tmp_path):
    # Setup workspace
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    file1 = workspace / "file1.py"
    file1.write_text("old content 1")
    file2 = workspace / "file2.py"
    file2.write_text("old content 2")

    # Mock AI response
    mock_change = FileChange(
        path="file1.py",
        new_content="new content 1",
        reasoning="Applied step 1"
    )

    # Mock test run
    mock_test_run = MagicMock(spec=TestRun)
    mock_test_run.id = "test_run_1"
    mock_test_run.status = "success"

    with patch("backend.app.agents.implementation.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = [
            mock_change,
            FileChange(path="file2.py", new_content="new content 2", reasoning="Applied step 2")
        ]

        with patch("backend.app.agents.implementation.test_agent.run_tests", new_callable=AsyncMock) as mock_run_tests:
            mock_run_tests.return_value = mock_test_run

            result = await agent.implement_solution(
                db=mock_db,
                repository=mock_repo,
                plan=mock_plan,
                contribution=mock_contribution,
                workspace_path=workspace,
                test_command="pytest"
            )

            assert result.success is True
            assert len(result.files_modified) == 2
            assert "file1.py" in result.files_modified
            assert "file2.py" in result.files_modified
            assert file1.read_text() == "new content 1"
            assert file2.read_text() == "new content 2"
            assert result.test_run_id == "test_run_1"

@pytest.mark.asyncio
async def test_implement_solution_partial_failures(agent, mock_db, mock_repo, mock_plan, mock_contribution, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    # file1.py exists
    file1 = workspace / "file1.py"
    file1.write_text("old content 1")
    # file2.py does NOT exist (skipped)

    with patch("backend.app.agents.implementation.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:
        # AI returns empty content for file1 (skipped)
        mock_chat.return_value = FileChange(path="file1.py", new_content="", reasoning="nothing")

        result = await agent.implement_solution(
            db=mock_db,
            repository=mock_repo,
            plan=mock_plan,
            contribution=mock_contribution,
            workspace_path=workspace
        )

        assert result.success is False
        assert len(result.files_modified) == 0

@pytest.mark.asyncio
async def test_implement_solution_test_failure(agent, mock_db, mock_repo, mock_plan, mock_contribution, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    file1 = workspace / "file1.py"
    file1.write_text("old content")

    mock_test_run = MagicMock(spec=TestRun)
    mock_test_run.id = "test_run_fail"
    mock_test_run.status = "failed"

    with patch("backend.app.agents.implementation.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = FileChange(path="file1.py", new_content="new content", reasoning="changed")

        with patch("backend.app.agents.implementation.test_agent.run_tests", new_callable=AsyncMock) as mock_run_tests:
            mock_run_tests.return_value = mock_test_run

            result = await agent.implement_solution(
                db=mock_db,
                repository=mock_repo,
                plan=mock_plan,
                contribution=mock_contribution,
                workspace_path=workspace,
                test_command="pytest"
            )

            assert result.success is False
            assert result.test_run_id == "test_run_fail"

@pytest.mark.asyncio
async def test_implement_solution_ai_error(agent, mock_db, mock_repo, mock_plan, mock_contribution, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    file1 = workspace / "file1.py"
    file1.write_text("old content")

    with patch("backend.app.agents.implementation.ai_gateway.chat_structured", side_effect=Exception("AI Down")):
        result = await agent.implement_solution(
            db=mock_db,
            repository=mock_repo,
            plan=mock_plan,
            contribution=mock_contribution,
            workspace_path=workspace
        )
        assert len(result.files_modified) == 0
        assert result.success is False

@pytest.mark.asyncio
async def test_implement_solution_context_inclusion(agent, mock_db, mock_repo, mock_plan, mock_contribution, tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    file1 = workspace / "file1.py"
    file1.write_text("old content")

    with patch("backend.app.agents.implementation.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = FileChange(path="file1.py", new_content="new", reasoning="r")

        await agent.implement_solution(
            db=mock_db,
            repository=mock_repo,
            plan=mock_plan,
            contribution=mock_contribution,
            workspace_path=workspace,
            debugging_context="Fix the syntax error",
            review_feedback="Use more comments"
        )

        args, kwargs = mock_chat.call_args
        prompt = kwargs["request"].messages[1].content
        assert "PREVIOUS FAILURE CONTEXT:\nFix the syntax error" in prompt
        assert "CODE REVIEW FEEDBACK:\nUse more comments" in prompt
