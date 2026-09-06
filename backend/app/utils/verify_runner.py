import asyncio
import sys
from pathlib import Path
from backend.app.sandbox import command_runner, SecurityPolicy
from backend.app.api.errors import LoomError
from backend.app.utils.logging import logger

async def verify_runner_logic():
    logger.info("Verifying CommandRunner security policy...")

    # 1. Test Permitted Command
    assert command_runner.policy.is_command_permitted("python --version")
    assert command_runner.policy.is_command_permitted("./gradlew test")
    assert command_runner.policy.is_command_permitted("npm install")

    # 2. Test Blocked Command
    assert not command_runner.policy.is_command_permitted("curl google.com")
    assert not command_runner.policy.is_command_permitted("cat /etc/passwd")
    assert not command_runner.policy.is_command_permitted("rm -rf / --no-preserve-root")

    logger.info("Security policy logic verified.")

    # 3. Test Runner Execution (Simulation of exception for blocked command)
    try:
        await command_runner.run(Path("."), "curl evil.com")
    except LoomError as e:
        assert e.code == "SECURITY_POLICY_VIOLATION"
        logger.info("Blocked command exception verified.")

    logger.info("CommandRunner verification successful.")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_runner_logic())
    if not success:
        sys.exit(1)
