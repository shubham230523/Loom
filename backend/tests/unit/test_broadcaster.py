import pytest
from unittest.mock import AsyncMock, MagicMock
from backend.app.utils.broadcaster import AgentBroadcaster

@pytest.mark.asyncio
async def test_broadcaster_workflow():
    broadcaster = AgentBroadcaster()
    rid = "run1"
    ws1 = AsyncMock()
    ws2 = AsyncMock()

    # Connect
    await broadcaster.connect(rid, ws1)
    await broadcaster.connect(rid, ws2)
    assert len(broadcaster.active_connections[rid]) == 2

    # Broadcast success
    await broadcaster.broadcast(rid, {"msg": "hi"})
    ws1.send_json.assert_called_with({"msg": "hi"})
    ws2.send_json.assert_called_with({"msg": "hi"})

    # Broadcast partial failure
    ws1.send_json.side_effect = Exception("Fail")
    await broadcaster.broadcast(rid, {"msg": "err"})
    assert ws2.send_json.called

    # Disconnect
    broadcaster.disconnect(rid, ws1)
    assert len(broadcaster.active_connections[rid]) == 1
    broadcaster.disconnect(rid, ws2)
    assert rid not in broadcaster.active_connections
