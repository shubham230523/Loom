import pytest
from pathlib import Path
from backend.app.repository.service import repository_service, Workspace

@pytest.mark.asyncio
async def test_discover_files_filtering(tmp_path):
    """Verify that discover_files respects ignored directories and file sizes."""
    # Setup mock workspace
    ws_path = tmp_path / "test_repo"
    ws_path.mkdir()
    (ws_path / "src").mkdir()
    (ws_path / ".git").mkdir()
    (ws_path / "src" / "main.py").write_text("print('hello')")
    (ws_path / ".git" / "config").write_text("ignored")
    (ws_path / "large_file.bin").write_bytes(b"0" * (1024 * 1024 * 2)) # 2MB, limit is 1MB

    ws = Workspace(workspace_id="test")
    ws.path = ws_path

    files = await repository_service.discover_files(ws)

    paths = [f["path"] for f in files]
    assert "src/main.py" in paths
    assert ".git/config" not in paths
    assert "large_file.bin" not in paths

@pytest.mark.asyncio
async def test_detect_build_system_python(tmp_path):
    """Verify detection of Python build system markers."""
    ws_path = tmp_path / "py_repo"
    ws_path.mkdir()
    (ws_path / "requirements.txt").write_text("fastapi")

    ws = Workspace(workspace_id="test")
    ws.path = ws_path

    build_info = await repository_service.detect_build_system(ws)
    assert "python" in build_info["systems"]
    assert build_info["primary_language"] == "Python"

@pytest.mark.asyncio
async def test_detect_build_system_node(tmp_path):
    """Verify detection of Node.js build system markers."""
    ws_path = tmp_path / "node_repo"
    ws_path.mkdir()
    (ws_path / "package.json").write_text('{"name": "test"}')

    ws = Workspace(workspace_id="test")
    ws.path = ws_path

    build_info = await repository_service.detect_build_system(ws)
    assert "npm" in build_info["systems"]
    assert build_info["primary_language"] == "JavaScript/TypeScript"
