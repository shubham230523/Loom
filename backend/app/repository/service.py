import os
import shutil
import asyncio
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from backend.app.config import settings
from backend.app.api.errors import LoomError
from backend.app.utils.logging import logger

class Workspace:
    def __init__(self, workspace_id: Optional[str] = None):
        self.id = workspace_id or str(uuid.uuid4())
        self.path = Path(settings.WORKSPACE_BASE_DIR) / self.id

    async def create(self):
        """Creates the workspace directory"""
        os.makedirs(self.path, exist_ok=True)
        logger.info(f"Created workspace at {self.path}")

    async def cleanup(self):
        """Removes the workspace directory and all its contents"""
        if self.path.exists():
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, shutil.rmtree, self.path)
            logger.info(f"Cleaned up workspace at {self.path}")

    def get_size_mb(self) -> float:
        """Returns the size of the workspace in Megabytes"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size / (1024 * 1024)

class RepositoryService:
    async def clone_repository(
        self,
        repo_url: str,
        access_token: str,
        workspace: Workspace
    ) -> Path:
        """
        Clones a repository into a workspace with security limits.
        """
        await workspace.create()

        # Use token in URL for authentication
        # Format: https://<token>@github.com/owner/repo.git
        authenticated_url = repo_url.replace("https://", f"https://{access_token}@")

        # Build git clone command with shallow clone for performance/size
        cmd = [
            "git", "clone",
            "--depth", "1",
            "--single-branch",
            authenticated_url,
            str(workspace.path)
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                # Enforce timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=settings.CLONE_TIMEOUT_SECONDS
                )

                if process.returncode != 0:
                    error_msg = stderr.decode().strip()
                    logger.error(f"Git clone failed: {error_msg}")
                    raise LoomError(f"Failed to clone repository: {error_msg}", status_code=500)

                # Check size limits
                size_mb = workspace.get_size_mb()
                if size_mb > settings.MAX_REPO_SIZE_MB:
                    logger.warning(f"Repository size {size_mb}MB exceeds limit {settings.MAX_REPO_SIZE_MB}MB")
                    await workspace.cleanup()
                    raise LoomError(
                        f"Repository too large ({round(size_mb, 2)}MB). Limit is {settings.MAX_REPO_SIZE_MB}MB.",
                        status_code=413
                    )

                logger.info(f"Successfully cloned repository into {workspace.path} ({round(size_mb, 2)}MB)")
                return workspace.path

            except asyncio.TimeoutError:
                process.kill()
                await workspace.cleanup()
                logger.error(f"Git clone timed out after {settings.CLONE_TIMEOUT_SECONDS}s")
                raise LoomError("Repository clone timed out", status_code=504)

        except Exception as e:
            if not isinstance(e, LoomError):
                logger.error(f"Unexpected error during clone: {str(e)}")
                await workspace.cleanup()
                raise LoomError(f"Repository clone failed: {str(e)}", status_code=500)
            raise

    async def discover_files(self, workspace: Workspace) -> List[Dict[str, Any]]:
        """
        Walks through the workspace and discovers files and directories.
        Applies security filters for ignored paths and oversized files.
        """
        if not workspace.path.exists():
            raise LoomError("Workspace path does not exist", status_code=404)

        discovered = []
        base_path = workspace.path

        for root, dirs, files in os.walk(base_path):
            # In-place modification of dirs to skip ignored directories
            dirs[:] = [d for d in dirs if d not in settings.IGNORED_DIRECTORIES]

            rel_root = os.path.relpath(root, base_path)
            if rel_root == ".":
                rel_root = ""

            # Add directories (except root)
            if rel_root:
                discovered.append({
                    "path": rel_root.replace("\\", "/"),
                    "name": os.path.basename(root),
                    "type": "directory",
                    "size_kb": 0,
                    "extension": ""
                })

            for file in files:
                if file in settings.IGNORED_FILES:
                    continue

                file_path = os.path.join(root, file)
                rel_file_path = os.path.relpath(file_path, base_path).replace("\\", "/")

                try:
                    file_stat = os.stat(file_path)
                    size_kb = file_stat.st_size / 1024

                    # Filter oversized files
                    if size_kb > settings.MAX_FILE_SIZE_KB:
                        logger.debug(f"Skipping oversized file: {rel_file_path} ({round(size_kb, 2)}KB)")
                        continue

                    discovered.append({
                        "path": rel_file_path,
                        "name": file,
                        "type": "file",
                        "size_kb": round(size_kb, 2),
                        "extension": os.path.splitext(file)[1].lower()
                    })
                except Exception as e:
                    logger.warning(f"Failed to stat file {rel_file_path}: {str(e)}")

        return discovered

repository_service = RepositoryService()
