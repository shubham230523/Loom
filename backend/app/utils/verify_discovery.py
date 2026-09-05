import asyncio
import sys
import os
from backend.app.repository import repository_service, Workspace
from backend.app.config import settings
from backend.app.utils.logging import logger

async def verify_discovery_logic():
    # Setup a test workspace with some files
    ws = Workspace(workspace_id="test_verify_discovery")
    await ws.create()

    try:
        # Create dummy directory structure
        os.makedirs(ws.path / "src", exist_ok=True)
        os.makedirs(ws.path / ".git", exist_ok=True)
        os.makedirs(ws.path / "node_modules", exist_ok=True)

        # Create some files
        with open(ws.path / "README.md", "w") as f:
            f.write("# Test Project")

        with open(ws.path / "src" / "main.py", "w") as f:
            f.write("print('hello')")

        with open(ws.path / ".gitignore", "w") as f:
            f.write(".git")

        with open(ws.path / "large_file.bin", "wb") as f:
            f.write(os.urandom(2 * 1024 * 1024)) # 2MB file

        # Discover files
        files = await repository_service.discover_files(ws)

        # Verify filters
        paths = [f["path"] for f in files]

        logger.info(f"Discovered paths: {paths}")

        # Check if basic files are present
        assert "README.md" in paths
        assert "src/main.py" in paths
        assert "src" in paths

        # Check if ignored directories are filtered
        assert ".git" not in paths
        assert "node_modules" not in paths

        # Check if oversized files are filtered
        assert "large_file.bin" not in paths

        logger.info("File discovery verification successful.")
        return True

    except Exception as e:
        logger.error(f"File discovery verification failed: {str(e)}")
        return False
    finally:
        await ws.cleanup()

if __name__ == "__main__":
    if sys.platform == "win32":
        settings.WORKSPACE_BASE_DIR = os.path.join(os.getcwd(), "test_workspaces")

    success = asyncio.run(verify_discovery_logic())
    if not success:
        sys.exit(1)
