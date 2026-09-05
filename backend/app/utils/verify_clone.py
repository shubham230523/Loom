import asyncio
import sys
import os
from backend.app.repository import repository_service, Workspace
from backend.app.config import settings
from backend.app.utils.logging import logger

async def verify_clone_logic():
    # Setup a test workspace
    ws = Workspace(workspace_id="test_verify_clone")

    # Check if git is available
    import subprocess
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        logger.info("Git is available.")
    except Exception:
        logger.error("Git is not installed or not in PATH.")
        return False

    # Verify base dir exists or can be created
    try:
        os.makedirs(settings.WORKSPACE_BASE_DIR, exist_ok=True)
        logger.info(f"Workspace base directory verified: {settings.WORKSPACE_BASE_DIR}")
    except Exception as e:
        logger.error(f"Failed to verify workspace base directory: {str(e)}")
        return False

    # We won't actually clone without a token, but we verify the workspace lifecycle
    try:
        await ws.create()
        if ws.path.exists():
            logger.info("Workspace creation verified.")
            size = ws.get_size_mb()
            logger.info(f"Workspace size check verified: {size}MB")
            await ws.cleanup()
            if not ws.path.exists():
                logger.info("Workspace cleanup verified.")
                return True
        return False
    except Exception as e:
        logger.error(f"Workspace lifecycle verification failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Temporarily adjust settings for test if needed
    if sys.platform == "win32":
        settings.WORKSPACE_BASE_DIR = os.path.join(os.getcwd(), "test_workspaces")

    success = asyncio.run(verify_clone_logic())
    if not success:
        sys.exit(1)
