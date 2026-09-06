import asyncio
import sys
import os
import shutil
from backend.app.repository import repository_service, Workspace
from backend.app.config import settings
from backend.app.utils.logging import logger

async def verify_workspace_logic():
    ws = Workspace(workspace_id="test_verify_workspace")
    # Cleanup previous if exists
    if ws.path.exists():
        def remove_readonly(func, path, excinfo):
            os.chmod(path, 0o777)
            func(path)
        shutil.rmtree(ws.path, onerror=remove_readonly)

    await ws.create()

    try:
        # Initialize a dummy git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=str(ws.path), check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "loom@example.com"], cwd=str(ws.path), check=True)
        subprocess.run(["git", "config", "user.name", "Loom Bot"], cwd=str(ws.path), check=True)

        # Need at least one commit to create a branch
        test_file = ws.path / "README.md"
        with open(test_file, "w") as f:
            f.write("# Test")

        subprocess.run(["git", "add", "."], cwd=str(ws.path), check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=str(ws.path), check=True)

        # 1. Verify branch creation
        branch_name = "ai/123-test-branch"
        await repository_service.create_contribution_branch(ws, branch_name)

        # Verify current branch
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(ws.path), check=True, capture_output=True)
        current_branch = result.stdout.decode().strip()
        logger.info(f"Current branch: {current_branch}")
        assert current_branch == branch_name

        logger.info("Workspace branch creation verification successful.")
        return True

    except Exception as e:
        logger.error(f"Workspace verification failed: {str(e)}")
        return False
    finally:
        await ws.cleanup()

if __name__ == "__main__":
    if sys.platform == "win32":
        settings.WORKSPACE_BASE_DIR = os.path.join(os.getcwd(), "test_workspaces")

    success = asyncio.run(verify_workspace_logic())
    if not success:
        sys.exit(1)
