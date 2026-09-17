import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import io
import docker
from backend.app.sandbox.manager import SandboxManager, SandboxResult, LoomError

@pytest.fixture
def manager():
    with patch("docker.from_env") as mock_env:
        return SandboxManager()

@pytest.mark.asyncio
async def test_run_in_sandbox_success(manager):
    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [b"stdout", b"stderr"]

    manager.client = MagicMock()
    manager.client.containers.create.return_value = mock_container

    with patch.object(manager, "_create_tar_stream", return_value=b"tar"):
        result = await manager.run_in_sandbox(Path("/tmp"), "ls")

        assert result.exit_code == 0
        assert result.stdout == "stdout"
        assert result.stderr == "stderr"
        manager.client.containers.create.assert_called_once()
        mock_container.start.assert_called_once()
        mock_container.remove.assert_called_once()

@pytest.mark.asyncio
async def test_run_in_sandbox_no_client(manager):
    manager.client = None
    with pytest.raises(Exception) as exc:
        await manager.run_in_sandbox(Path("/tmp"), "ls")
    assert "Docker is not available" in str(exc.value)

@pytest.mark.asyncio
async def test_run_in_sandbox_image_not_found(manager):
    manager.client = MagicMock()
    manager.client.images.get.side_effect = docker.errors.ImageNotFound("not found")

    mock_container = MagicMock()
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.side_effect = [b"stdout", b"stderr"]
    manager.client.containers.create.return_value = mock_container

    with patch.object(manager, "_create_tar_stream", return_value=b"tar"):
        result = await manager.run_in_sandbox(Path("/tmp"), "ls")
        assert result.exit_code == 0
        manager.client.images.pull.assert_called_once()

@pytest.mark.asyncio
async def test_run_in_sandbox_timeout(manager):
    manager.client = MagicMock()
    mock_container = MagicMock()
    mock_container.wait.side_effect = Exception("Timeout exception")
    mock_container.logs.side_effect = [b"partial stdout", b"partial stderr"]
    manager.client.containers.create.return_value = mock_container

    with patch.object(manager, "_create_tar_stream", return_value=b"tar"):
        result = await manager.run_in_sandbox(Path("/tmp"), "ls")
        assert result.timed_out is True
        assert result.exit_code == 137
        mock_container.kill.assert_called_once()

@pytest.mark.asyncio
async def test_run_in_sandbox_general_exception(manager):
    manager.client = MagicMock()
    manager.client.containers.create.side_effect = Exception("Creation failed")

    with pytest.raises(LoomError) as exc:
        await manager.run_in_sandbox(Path("/tmp"), "ls")
    assert "Sandbox execution failed" in str(exc.value)

def test_create_tar_stream_and_extract(manager, tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello")

    stream = manager._create_tar_stream(tmp_path)
    assert stream.getvalue() != b""

    extract_path = tmp_path / "extract"
    extract_path.mkdir()
    manager._extract_tar_stream(stream.getvalue(), extract_path)
    assert (extract_path / "test.txt").read_text() == "hello"

@pytest.mark.asyncio
async def test_get_workspace_files(manager, tmp_path):
    manager.client = MagicMock()
    mock_container = MagicMock()
    manager.client.containers.get.return_value = mock_container

    # Create valid tar bytes containing a 'workspace/file.txt'
    import tarfile
    tar_io = io.BytesIO()
    with tarfile.open(fileobj=tar_io, mode="w") as tar:
        info = tarfile.TarInfo(name="workspace/file.txt")
        content = b"content"
        info.size = len(content)
        tar.addfile(info, io.BytesIO(content))

    mock_container.get_archive.return_value = ([tar_io.getvalue()], {})

    target_path = tmp_path / "target"
    target_path.mkdir()

    await manager.get_workspace_files("c123", target_path)
    assert (target_path / "file.txt").read_text() == "content"

@pytest.mark.asyncio
async def test_get_workspace_files_no_client(manager, tmp_path):
    manager.client = None
    res = await manager.get_workspace_files("c123", tmp_path)
    assert res is None
