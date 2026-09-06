from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from backend.app.utils.broadcaster import agent_broadcaster
from backend.app.utils.logging import logger
from backend.app.security.auth import get_current_user
from backend.app.database import SessionLocal, AgentRun, Contribution
from sqlalchemy import select
from uuid import UUID

router = APIRouter()

@router.websocket("/agents/{agent_run_id}")
async def agent_ws_endpoint(
    websocket: WebSocket,
    agent_run_id: str,
    token: str = Query(...)
):
    """
    WebSocket endpoint with token-based authorization.
    Verifies the user has permission to view events for this agent run.
    """
    # 1. Manually verify token for WS
    from backend.app.security.auth import decode_token
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008) # Policy Violation
            return
    except Exception:
        await websocket.close(code=1008)
        return

    # 2. Verify Authorization (Does this run belong to the user?)
    async with SessionLocal() as db:
        try:
            query = (
                select(AgentRun)
                .join(Contribution)
                .where(
                    AgentRun.id == UUID(agent_run_id),
                    Contribution.user_id == UUID(user_id)
                )
            )
            result = await db.execute(query)
            run = result.scalar_one_or_none()

            if not run:
                await websocket.close(code=1008)
                return
        except Exception:
            await websocket.close(code=1008)
            return

    # 3. Connect to broadcaster
    await agent_broadcaster.connect(agent_run_id, websocket)
    try:
        while True:
            # Wait for any messages from client
            await websocket.receive_text()
    except WebSocketDisconnect:
        agent_broadcaster.disconnect(agent_run_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for {agent_run_id}: {str(e)}")
        agent_broadcaster.disconnect(agent_run_id, websocket)
