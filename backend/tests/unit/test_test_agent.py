import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch
from backend.app.agents.test_agent import TestAgent
from backend.app.database.models import Contribution
from backend.app.sandbox.manager import SandboxResult

@pytest.mark.asyncio
async def test_run_tests_success():
    agent = TestAgent()
    db = AsyncMock()
    contribution = Contribution(id="c-id")
    workspace_path = Path("/tmp")

    mock_result = SandboxResult(
        exit_code=0,
        stdout="All tests passed",
        stderr="",
        duration=2.5,
        timed_out=False
    )

    with patch("backend.app.sandbox.command_runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result

        res = await agent.run_tests(db, contribution, workspace_path, "pytest")

        assert res.status == "success"
        assert res.exit_code == 0
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_run_tests_failure():
    agent = TestAgent()
    db = AsyncMock()
    contribution = Contribution(id="c-id")
    workspace_path = Path("/tmp")

    mock_result = SandboxResult(
        exit_code=1,
        stdout="Test failed",
        stderr="Error line",
        duration=1.2,
        timed_out=False
    )

    with patch("backend.app.sandbox.command_runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result

        res = await agent.run_tests(db, contribution, workspace_path, "pytest")

        assert res.status == "failure"
        assert res.exit_code == 1

@pytest.mark.asyncio
async def test_run_tests_timeout():
    agent = TestAgent()
    db = AsyncMock()
    contribution = Contribution(id="c-id")
    workspace_path = Path("/tmp")

    mock_result = SandboxResult(
        exit_code=-1,
        stdout="",
        stderr="",
        duration=30.0,
        timed_out=True
    )

    with patch("backend.app.sandbox.command_runner.run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result

        res = await agent.run_tests(db, contribution, workspace_path, "pytest")

        assert res.status == "error"
