from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.database import TestRun, Contribution
from backend.app.sandbox import command_runner, SandboxResult
from backend.app.services.agent_run_service import agent_run_service
from backend.app.utils.logging import logger
from backend.app.config import settings

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
        Optimizes the command based on settings (e.g., compilation check only).
        """
        # Handle Skip Mode
        if settings.SANDBOX_TEST_LEVEL == "none":
            logger.info("TestAgent: Skipping tests as per SANDBOX_TEST_LEVEL setting.")
            test_run = TestRun(
                contribution_id=contribution.id,
                command="SKIPPED",
                exit_code=0,
                status="success",
                stdout="Tests skipped by configuration"
            )
            db.add(test_run)
            await db.commit()
            await db.refresh(test_run)
            return test_run

        # Optimize Gradle commands
        if "./gradlew test" in test_command or "gradle test" in test_command:
            optimization_flags = " --parallel --build-cache --configuration-cache -x lint -x detekt"

            if settings.SANDBOX_TEST_LEVEL == "compilation_only":
                # Replace 'test' with 'classes' which just compiles everything (fastest reliable check)
                test_command = test_command.replace("test", f"classes{optimization_flags}")
                logger.info(f"TestAgent: Switched to compilation check: {test_command}")
            else:
                if not any(f in test_command for f in ["--tests", "-x"]):
                    test_command = test_command.replace("test", f"test{optimization_flags}")
                    logger.info(f"TestAgent: Optimized broad Gradle command to: {test_command}")

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
