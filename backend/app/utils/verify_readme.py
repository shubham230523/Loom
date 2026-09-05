import asyncio
import sys
import os
from backend.app.repository import repository_service, Workspace
from backend.app.config import settings
from backend.app.utils.logging import logger

async def verify_readme_logic():
    ws = Workspace(workspace_id="test_verify_readme")
    await ws.create()

    try:
        # Create a sample README.md
        readme_content = """
# Loom Project

Loom is an autonomous collaboration platform.

## Installation
Run `pip install loom` to install.

## Usage
Start Loom by running `loom start`.

## Architecture
Loom uses a distributed agent system.

## Contributing
Follow the development instructions.
"""
        with open(ws.path / "README.md", "w") as f:
            f.write(readme_content)

        # Extract info
        info = await repository_service.extract_readme_info(ws)

        logger.info(f"Extracted info: {info}")

        assert info["found"] == True
        sections = info["sections"]
        assert "autonomous collaboration platform" in sections["description"]
        assert "pip install loom" in sections["installation"]
        assert "loom start" in sections["usage"]
        assert "distributed agent system" in sections["architecture"]
        assert "development instructions" in sections["development"]

        logger.info("README extraction verification successful.")
        return True

    except Exception as e:
        logger.error(f"README extraction verification failed: {str(e)}")
        return False
    finally:
        await ws.cleanup()

if __name__ == "__main__":
    if sys.platform == "win32":
        settings.WORKSPACE_BASE_DIR = os.path.join(os.getcwd(), "test_workspaces")

    success = asyncio.run(verify_readme_logic())
    if not success:
        sys.exit(1)
