import asyncio
import sys
import os
import json
from backend.app.repository import repository_service, Workspace
from backend.app.config import settings
from backend.app.utils.logging import logger

async def verify_test_detection_logic():
    ws = Workspace(workspace_id="test_verify_tests")
    await ws.create()

    try:
        # 1. Simulate a JS project with Jest
        with open(ws.path / "package.json", "w") as f:
            json.dump({
                "name": "test-js",
                "scripts": {"test": "jest"},
                "devDependencies": {"jest": "^29.0.0"}
            }, f)

        build_info = await repository_service.detect_build_system(ws)
        test_info = await repository_service.detect_test_system(ws, build_info)
        logger.info(f"JS Test Detection: {test_info}")
        assert "jest" in test_info["frameworks"]
        assert "npm test" in test_info["test_commands"]

        # 2. Simulate a Python project with Pytest
        await ws.cleanup()
        await ws.create()
        with open(ws.path / "requirements.txt", "w") as f:
            f.write("pytest")
        with open(ws.path / "pytest.ini", "w") as f:
            f.write("[pytest]")

        build_info = await repository_service.detect_build_system(ws)
        test_info = await repository_service.detect_test_system(ws, build_info)
        logger.info(f"Python Test Detection: {test_info}")
        assert "pytest" in test_info["frameworks"]
        assert "pytest" in test_info["test_commands"]

        # 3. Simulate a Gradle project
        await ws.cleanup()
        await ws.create()
        with open(ws.path / "build.gradle", "w") as f:
            f.write("")
        with open(ws.path / "gradlew", "w") as f:
            f.write("")

        build_info = await repository_service.detect_build_system(ws)
        test_info = await repository_service.detect_test_system(ws, build_info)
        logger.info(f"Gradle Test Detection: {test_info}")
        assert "junit" in test_info["frameworks"]
        assert "./gradlew test" in test_info["test_commands"]

        logger.info("Test system detection verification successful.")
        return True

    except Exception as e:
        logger.error(f"Test system detection verification failed: {str(e)}")
        return False
    finally:
        await ws.cleanup()

if __name__ == "__main__":
    if sys.platform == "win32":
        settings.WORKSPACE_BASE_DIR = os.path.join(os.getcwd(), "test_workspaces")

    success = asyncio.run(verify_test_detection_logic())
    if not success:
        sys.exit(1)
