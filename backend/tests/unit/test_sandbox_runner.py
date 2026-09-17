import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path
from backend.app.sandbox.runner import CommandRunner, LoomError

@pytest.mark.asyncio
async def test_command_runner_permitted():
    runner = CommandRunner()
    mock_result = AsyncMock()
    with patch("backend.app.sandbox.runner.sandbox_manager.run_in_sandbox", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = mock_result
        res = await runner.run(Path("/tmp"), "ls")
        assert res == mock_result
        mock_run.assert_called_once()

@pytest.mark.asyncio
async def test_command_runner_blocked():
    runner = CommandRunner()
    with pytest.raises(LoomError, match="not permitted"):
        await runner.run(Path("/tmp"), "curl http://bad")
