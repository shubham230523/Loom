import asyncio
from typing import Dict, List, Any
from fastapi import WebSocket
from backend.app.utils.logging import logger

class AgentBroadcaster:
    def __init__(self):
        # agent_run_id -> list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, agent_run_id: str, websocket: WebSocket):
        await websocket.accept()
        if agent_run_id not in self.active_connections:
            self.active_connections[agent_run_id] = []
        self.active_connections[agent_run_id].append(websocket)
        logger.info(f"WebSocket connected for agent run {agent_run_id}")

    def disconnect(self, agent_run_id: str, websocket: WebSocket):
        if agent_run_id in self.active_connections:
            self.active_connections[agent_run_id].remove(websocket)
            if not self.active_connections[agent_run_id]:
                del self.active_connections[agent_run_id]
        logger.info(f"WebSocket disconnected for agent run {agent_run_id}")

    async def broadcast(self, agent_run_id: str, event: Dict[str, Any]):
        if agent_run_id in self.active_connections:
            # Create a copy of the list to iterate over to avoid modification errors
            connections = list(self.active_connections[agent_run_id])
            for websocket in connections:
                try:
                    await websocket.send_json(event)
                except Exception as e:
                    logger.warning(f"Failed to send WebSocket message: {str(e)}")
                    # Connection might be closed, it will be removed on next heartbeat/disconnect

agent_broadcaster = AgentBroadcaster()
