import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.utils.verify_workspace import verify_workspace_logic

@pytest.mark.asyncio
async def test_verify_workspace_logic_success():
    with patch("backend.app.utils.verify_workspace.Workspace") as mock_ws_class, \
         patch("backend.app.utils.verify_workspace.repository_service", new_callable=AsyncMock) as mock_svc, \
         patch("subprocess.run") as mock_run:

        mock_ws = mock_ws_class.return_value
        mock_ws.path.exists.return_value = False
        mock_ws.create = AsyncMock()
        mock_ws.cleanup = AsyncMock()

        # Mock subprocess.run for git branch check
        mock_res = MagicMock()
        mock_res.stdout = b"ai/123-test-branch\n"
        mock_run.return_value = mock_res

        res = await verify_workspace_logic()
        assert res is True

@pytest.mark.asyncio
async def test_verify_workspace_logic_failure():
    with patch("backend.app.utils.verify_workspace.Workspace") as mock_ws_class, \
         patch("subprocess.run", side_effect=Exception("Git Fail")):
        mock_ws = mock_ws_class.return_value
        mock_ws.path.exists.return_value = False
        mock_ws.create = AsyncMock()
        mock_ws.cleanup = AsyncMock()

        res = await verify_workspace_logic()
        assert res is False
