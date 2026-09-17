import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.websockets import WebSocketDisconnect
from backend.app.api.ws import agent_ws_endpoint

@pytest.mark.asyncio
async def test_agent_ws_endpoint_success():
    run_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    token = "valid_token"

    mock_websocket = AsyncMock()
    mock_websocket.receive_text.side_effect = WebSocketDisconnect()

    with patch("backend.app.security.auth.decode_token", return_value={"sub": user_id}), \
         patch("backend.app.api.ws.SessionLocal") as mock_session_factory, \
         patch("backend.app.api.ws.agent_broadcaster", new_callable=AsyncMock) as mock_broadcaster:

        mock_db = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_db
        mock_db.execute.return_value = MagicMock(scalar_one_or_none=lambda: MagicMock())

        await agent_ws_endpoint(mock_websocket, run_id, token)

        assert mock_broadcaster.connect.called
        assert mock_broadcaster.disconnect.called

@pytest.mark.asyncio
async def test_agent_ws_endpoint_no_user_id():
    mock_websocket = AsyncMock()
    with patch("backend.app.security.auth.decode_token", return_value={"sub": None}):
        await agent_ws_endpoint(mock_websocket, str(uuid.uuid4()), "token")
        mock_websocket.close.assert_called_once_with(code=1008)

@pytest.mark.asyncio
async def test_agent_ws_endpoint_decode_exception():
    mock_websocket = AsyncMock()
    with patch("backend.app.security.auth.decode_token", side_effect=Exception("Decode failed")):
        await agent_ws_endpoint(mock_websocket, str(uuid.uuid4()), "token")
        mock_websocket.close.assert_called_once_with(code=1008)

@pytest.mark.asyncio
async def test_agent_ws_endpoint_no_run_found():
    run_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    mock_websocket = AsyncMock()

    with patch("backend.app.security.auth.decode_token", return_value={"sub": user_id}), \
         patch("backend.app.api.ws.SessionLocal") as mock_session_factory:
        mock_db = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_db
        mock_db.execute.return_value = MagicMock(scalar_one_or_none=lambda: None)

        await agent_ws_endpoint(mock_websocket, run_id, "token")
        mock_websocket.close.assert_called_once_with(code=1008)

@pytest.mark.asyncio
async def test_agent_ws_endpoint_db_exception():
    run_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    mock_websocket = AsyncMock()

    with patch("backend.app.security.auth.decode_token", return_value={"sub": user_id}), \
         patch("backend.app.api.ws.SessionLocal") as mock_session_factory:
        mock_db = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_db
        mock_db.execute.side_effect = Exception("DB error")

        await agent_ws_endpoint(mock_websocket, run_id, "token")
        mock_websocket.close.assert_called_once_with(code=1008)

@pytest.mark.asyncio
async def test_agent_ws_endpoint_receive_general_exception():
    run_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    token = "valid_token"

    mock_websocket = AsyncMock()
    mock_websocket.receive_text.side_effect = Exception("General error")

    with patch("backend.app.security.auth.decode_token", return_value={"sub": user_id}), \
         patch("backend.app.api.ws.SessionLocal") as mock_session_factory, \
         patch("backend.app.api.ws.agent_broadcaster", new_callable=AsyncMock) as mock_broadcaster:

        mock_db = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_db
        mock_db.execute.return_value = MagicMock(scalar_one_or_none=lambda: MagicMock())

        await agent_ws_endpoint(mock_websocket, run_id, token)

        assert mock_broadcaster.connect.called
        assert mock_broadcaster.disconnect.called
