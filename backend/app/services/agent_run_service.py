from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import AgentRun, AgentEvent, SessionLocal
from backend.app.utils.broadcaster import agent_broadcaster
from backend.app.utils.logging import logger

class AgentRunService:
    async def create_agent_run(
        self,
        db: AsyncSession,
        contribution_id: UUID,
        agent_type: str
    ) -> AgentRun:
        run = AgentRun(
            contribution_id=contribution_id,
            agent_type=agent_type,
            status="running",
            started_at=datetime.now(timezone.utc)
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        await self.emit_event(
            db=db,
            agent_run_id=run.id,
            event_type="agent_started",
            message=f"{agent_type.capitalize()} agent started execution."
        )

        return run

    async def emit_event(
        self,
        db: AsyncSession,
        agent_run_id: UUID,
        event_type: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        event = AgentEvent(
            agent_run_id=agent_run_id,
            event_type=event_type,
            message=message,
            event_metadata=metadata
        )
        db.add(event)
        await db.commit()

        # Broadcast via WebSocket
        payload = {
            "agent_run_id": str(agent_run_id),
            "event_type": event_type,
            "message": message,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await agent_broadcaster.broadcast(str(agent_run_id), payload)
        logger.info(f"Agent Event Emitted: {event_type} - {message}")

    async def complete_run(self, db: AsyncSession, agent_run_id: UUID, success: bool = True):
        query = select(AgentRun).where(AgentRun.id == agent_run_id)
        result = await db.execute(query)
        run = result.scalar_one_or_none()

        if run:
            run.status = "completed" if success else "failed"
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()

            await self.emit_event(
                db=db,
                agent_run_id=agent_run_id,
                event_type="completed" if success else "failed",
                message=f"Agent execution {'completed successfully' if success else 'failed'}."
            )

agent_run_service = AgentRunService()
