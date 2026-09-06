import asyncio
import sys
import os
from backend.app.repository import repository_service, Workspace
from backend.app.config import settings
from backend.app.utils.logging import logger

async def verify_signals_logic():
    ws = Workspace(workspace_id="test_verify_signals")
    await ws.create()

    try:
        # 1. Create files with signals
        os.makedirs(ws.path / "src", exist_ok=True)

        # Python file with TODO and unimplemented
        with open(ws.path / "src" / "logic.py", "w") as f:
            f.write("""
def fast_logic():
    # TODO: optimize this loop
    pass

def missing():
    raise NotImplementedError()
""")

        # JS file with FIXME
        with open(ws.path / "src" / "api.js", "w") as f:
            f.write("""
// FIXME: handle auth properly
function callApi() {}
""")

        # 2. Detect signals
        signals = await repository_service.detect_code_signals(ws)
        logger.info(f"Detected signals: {signals}")

        types = [s["type"] for s in signals]
        assert "TODO" in types
        assert "FIXME" in types
        assert "UNIMPLEMENTED" in types

        # 3. Detect test gaps
        files_metadata = [
            {"path": "src/logic.py", "type": "file", "extension": ".py"},
            {"path": "src/api.js", "type": "file", "extension": ".js"}
        ]
        gaps = await repository_service.detect_test_gaps(ws, files_metadata)
        logger.info(f"Detected gaps: {gaps}")
        assert len(gaps) == 2

        logger.info("Code signals detection verification successful.")
        return True

    except Exception as e:
        logger.error(f"Code signals verification failed: {str(e)}")
        return False
    finally:
        await ws.cleanup()

if __name__ == "__main__":
    if sys.platform == "win32":
        settings.WORKSPACE_BASE_DIR = os.path.join(os.getcwd(), "test_workspaces")

    success = asyncio.run(verify_signals_logic())
    if not success:
        sys.exit(1)
