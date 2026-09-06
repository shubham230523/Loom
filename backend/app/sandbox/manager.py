import docker
import os
import tarfile
import io
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel
from backend.app.config import settings
from backend.app.utils.logging import logger
from backend.app.api.errors import LoomError

class SandboxResult(BaseModel):
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool

class SandboxManager:
    def __init__(self):
        try:
            # Check if we're on Windows or Unix to set the appropriate base_url if needed
            # but usually from_env() handles it if Docker is running.
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {str(e)}")
            self.client = None

    async def run_in_sandbox(
        self,
        workspace_path: Path,
        command: str,
        image: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> SandboxResult:
        """
        Executes a command inside a Docker sandbox with strict resource limits.
        """
        if not self.client:
            raise LoomError("Docker is not available for sandbox execution", status_code=500)

        image = image or settings.SANDBOX_IMAGE
        timeout = timeout or settings.SANDBOX_TIMEOUT

        # 1. Ensure image is available
        try:
            self.client.images.get(image)
        except docker.errors.ImageNotFound:
            logger.info(f"Pulling sandbox image: {image}")
            # Use run_in_executor for long-running sync call
            import asyncio
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.client.images.pull, image)

        # 2. Configure sandbox constraints
        # PIDs limit is supported in API 1.23+
        container_config = {
            "image": image,
            "command": ["sh", "-c", command],
            "cpu_period": 100000,
            "cpu_quota": int(settings.SANDBOX_CPU_LIMIT * 100000),
            "mem_limit": settings.SANDBOX_MEMORY_LIMIT,
            "pids_limit": settings.SANDBOX_PIDS_LIMIT,
            "network_mode": settings.SANDBOX_NETWORK_MODE,
            "privileged": False,
            "cap_drop": ["ALL"], # Drop all capabilities
            "security_opt": ["no-new-privileges"],
            "working_dir": "/workspace",
            "detach": True,
            "remove": False
        }

        # Disk limit requires specialized storage driver (overlay2 with xfs prpquota etc)
        # We'll omit it from general config to avoid errors on standard setups,
        # but the request mentioned it. Docker doesn't support easy disk limits on all hosts.

        container = None
        start_time = time.time()
        try:
            # 3. Create container
            container = self.client.containers.create(**container_config)

            # 4. Upload workspace files
            tar_stream = self._create_tar_stream(workspace_path)
            container.put_archive("/workspace", tar_stream)

            # 5. Start and wait
            container.start()

            status_code = -1
            timed_out = False
            try:
                # wait() is a blocking call, use run_in_executor
                import asyncio
                loop = asyncio.get_running_loop()
                wait_result = await loop.run_in_executor(None, lambda: container.wait(timeout=timeout))
                status_code = wait_result.get("StatusCode", -1)
            except Exception as e:
                logger.warning(f"Sandbox execution timed out: {str(e)}")
                container.kill()
                timed_out = True
                status_code = 137 # SIGKILL

            duration = time.time() - start_time
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

            return SandboxResult(
                exit_code=status_code,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                timed_out=timed_out
            )

        except Exception as e:
            logger.error(f"Sandbox execution error: {str(e)}")
            raise LoomError(f"Sandbox execution failed: {str(e)}", status_code=500)
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def _create_tar_stream(self, path: Path) -> io.BytesIO:
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as tar:
            if path.exists():
                for item in os.listdir(path):
                    item_path = path / item
                    tar.add(item_path, arcname=item)
        stream.seek(0)
        return stream

    def _extract_tar_stream(self, tar_data: bytes, target_path: Path):
        stream = io.BytesIO(tar_data)
        with tarfile.open(fileobj=stream, mode='r') as tar:
            tar.extractall(path=target_path)

    async def get_workspace_files(self, container_id: str, target_path: Path):
        """
        Retrieves the entire workspace directory from a container and extracts it.
        """
        if not self.client: return

        container = self.client.containers.get(container_id)
        # get_archive returns a tuple (stream, stat)
        bits, stat = container.get_archive("/workspace")

        # Collect all bits into a single byte string
        tar_data = b"".join(bits)

        # Extract to target path
        # Note: get_archive for /workspace includes the 'workspace/' prefix in the tar
        # so we extract to the parent of target_path or handle the prefix
        import shutil
        temp_extract = target_path.parent / f"extract_{container_id}"
        os.makedirs(temp_extract, exist_ok=True)

        self._extract_tar_stream(tar_data, temp_extract)

        # Move contents from temp_extract/workspace to target_path
        source_dir = temp_extract / "workspace"
        if source_dir.exists():
            for item in os.listdir(source_dir):
                s = source_dir / item
                d = target_path / item
                if s.is_dir():
                    if d.exists(): shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)

        shutil.rmtree(temp_extract)

sandbox_manager = SandboxManager()
