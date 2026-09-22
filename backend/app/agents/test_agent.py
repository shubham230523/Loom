from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import TestRun, Contribution
from backend.app.sandbox import command_runner, SandboxResult
from backend.app.services.agent_run_service import agent_run_service
from backend.app.utils.logging import logger

class TestAgent:
    async def run_tests(
        self,
        db: AsyncSession,
        contribution: Contribution,
        workspace_path: Path,
        test_command: str,
        agent_run_id: Optional[Any] = None
    ) -> TestRun:
        """
        Executes a test command in the sandbox and records the result.
        """
        logger.info(f"TestAgent: Executing tests for contribution {contribution.id}: {test_command}")

        if agent_run_id:
            await agent_run_service.emit_event(
                db=db,
                agent_run_id=agent_run_id,
                event_type="step_started",
                message=f"Executing validation command: {test_command}"
            )

        # 1. Execute in sandbox
        sandbox_result: SandboxResult = await command_runner.run(
            workspace_path=workspace_path,
            command=test_command
        )

        # 2. Emit logs to UI (Truncated for performance)
        if agent_run_id:
            if sandbox_result.stdout:
                # Capture last 5000 characters to avoid huge payload overhead
                stdout_tail = sandbox_result.stdout[-5000:]
                await agent_run_service.emit_event(
                    db=db,
                    agent_run_id=agent_run_id,
                    event_type="thinking_chunk",
                    message=f"\n--- TEST OUTPUT (Last 5k chars) ---\n{stdout_tail}"
                )
            if sandbox_result.stderr:
                stderr_tail = sandbox_result.stderr[-2000:]
                await agent_run_service.emit_event(
                    db=db,
                    agent_run_id=agent_run_id,
                    event_type="thinking_chunk",
                    message=f"\n--- TEST ERRORS ---\n{stderr_tail}"
                )

        # 3. Map status
        status = "success" if sandbox_result.exit_code == 0 else "failure"
        if sandbox_result.timed_out:
            status = "error"

        # 3. Persist record
        test_run = TestRun(
            contribution_id=contribution.id,
            command=test_command,
            exit_code=sandbox_result.exit_code,
            stdout=sandbox_result.stdout,
            stderr=sandbox_result.stderr,
            duration=sandbox_result.duration,
            status=status
        )

        db.add(test_run)
        await db.commit()
        await db.refresh(test_run)

        logger.info(f"TestAgent: Test execution finished with status {status}")
        return test_run

test_agent = TestAgent()
