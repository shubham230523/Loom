import pytest
from unittest.mock import AsyncMock, patch
from backend.app.agents.debugger import DebuggerAgent, DebuggingAnalysis
from backend.app.database.models import TestRun

@pytest.mark.asyncio
async def test_analyze_failure_success():
    agent = DebuggerAgent()
    test_run = TestRun(command="pytest", stdout="AssertionError\nExpected 2 got 1", stderr=None)

    mock_analysis = DebuggingAnalysis(
        root_cause_analysis="Wrong return value",
        suggested_fix="Change 1 to 2",
        affected_files=["main.py"]
    )

    with patch("backend.app.ai.gateway.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_analysis

        res = await agent.analyze_failure(test_run, "Plan", "Code")

        assert res.root_cause_analysis == "Wrong return value"
        mock_chat.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_failure_no_outputs():
    agent = DebuggerAgent()
    test_run = TestRun(command="pytest", stdout=None, stderr="Fatal error")

    mock_analysis = DebuggingAnalysis(
        root_cause_analysis="Fatal crash",
        suggested_fix="Fix syntax",
        affected_files=["main.py"]
    )

    with patch("backend.app.ai.gateway.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_analysis

        res = await agent.analyze_failure(test_run, "Plan", "Code")

        assert res.root_cause_analysis == "Fatal crash"
