from typing import Dict, Any, Optional
from pathlib import Path
from backend.app.sandbox.manager import sandbox_manager, SandboxResult
from backend.app.sandbox.policy import SecurityPolicy, default_policy
from backend.app.api.errors import LoomError
from backend.app.utils.logging import logger

class CommandRunner:
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or default_policy

    async def run(
        self,
        workspace_path: Path,
        command: str,
        image: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """
        Validates and executes a command in the sandbox.
        """
        # 1. Enforce Security Policy
        if not self.policy.is_command_permitted(command):
            logger.warning(f"Blocked prohibited command: {command}")
            raise LoomError(
                message=f"Command '{command}' is not permitted by the security policy",
                status_code=403,
                code="SECURITY_POLICY_VIOLATION"
            )

        logger.info(f"CommandRunner: Executing permitted command: {command}")

        # 2. Delegate to Sandbox Manager
        result = await sandbox_manager.run_in_sandbox(
            workspace_path=workspace_path,
            command=command,
            image=image,
            timeout=timeout
        )

        return result

# Global runner instance
command_runner = CommandRunner()
