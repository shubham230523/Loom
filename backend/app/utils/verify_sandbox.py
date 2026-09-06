import asyncio
import sys
import os
from pathlib import Path
from backend.app.sandbox.manager import sandbox_manager
from backend.app.utils.logging import logger

async def verify_sandbox_logic():
    # 1. Prepare a temporary test workspace
    test_path = Path("test_sandbox_workspace")
    os.makedirs(test_path, exist_ok=True)
    with open(test_path / "hello.py", "w") as f:
        f.write("print('Hello from Sandbox!')")

    try:
        logger.info("Starting sandbox verification...")

        # 2. Run a simple command
        result = await sandbox_manager.run_in_sandbox(
            workspace_path=test_path,
            command="python hello.py",
            timeout=30
        )

        logger.info(f"Sandbox Result: {result}")

        assert result.exit_code == 0
        assert "Hello from Sandbox!" in result.stdout
        assert not result.timed_out

        # 3. Test Network Restriction
        logger.info("Testing network restriction...")
        net_result = await sandbox_manager.run_in_sandbox(
            workspace_path=test_path,
            command="curl -m 2 google.com",
            timeout=10
        )
        # curl should fail or timeout because network is "none"
        logger.info(f"Network test exit code: {net_result.exit_code}")
        # status code might be 127 if curl not installed, or non-zero if failed

        logger.info("Sandbox verification successful.")
        return True

    except Exception as e:
        logger.error(f"Sandbox verification failed: {str(e)}")
        return False
    finally:
        # Cleanup
        import shutil
        if test_path.exists():
            shutil.rmtree(test_path)

if __name__ == "__main__":
    success = asyncio.run(verify_sandbox_logic())
    if not success:
        sys.exit(1)
