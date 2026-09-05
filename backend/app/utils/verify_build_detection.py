import asyncio
import sys
import os
from backend.app.repository import repository_service, Workspace
from backend.app.config import settings
from backend.app.utils.logging import logger

async def verify_build_detection_logic():
    ws = Workspace(workspace_id="test_verify_build")
    await ws.create()

    try:
        # 1. Simulate a JS/TypeScript project (npm + yarn)
        with open(ws.path / "package.json", "w") as f:
            f.write('{"name": "test"}')
        with open(ws.path / "yarn.lock", "w") as f:
            f.write("")

        info = await repository_service.detect_build_system(ws)
        logger.info(f"JS Project Detection: {info}")
        assert "npm" in info["systems"]
        assert "yarn" in info["systems"]
        assert info["primary_language"] == "JavaScript/TypeScript"
        assert info["has_lock_file"] == True

        # 2. Add Gradle markers
        with open(ws.path / "build.gradle", "w") as f:
            f.write("")
        with open(ws.path / "gradlew", "w") as f:
            f.write("")

        info = await repository_service.detect_build_system(ws)
        logger.info(f"Mixed Project Detection: {info}")
        assert "gradle" in info["systems"]
        assert info["has_wrapper"] == True

        # 3. Simulate Python project
        # Cleanup first
        await ws.cleanup()
        await ws.create()
        with open(ws.path / "requirements.txt", "w") as f:
            f.write("fastapi")

        info = await repository_service.detect_build_system(ws)
        logger.info(f"Python Project Detection: {info}")
        assert "python" in info["systems"]
        assert info["primary_language"] == "Python"

        logger.info("Build system detection verification successful.")
        return True

    except Exception as e:
        logger.error(f"Build system detection verification failed: {str(e)}")
        return False
    finally:
        await ws.cleanup()

if __name__ == "__main__":
    if sys.platform == "win32":
        settings.WORKSPACE_BASE_DIR = os.path.join(os.getcwd(), "test_workspaces")

    success = asyncio.run(verify_build_detection_logic())
    if not success:
        sys.exit(1)
