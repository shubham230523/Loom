import os
import shutil
import asyncio
import uuid
import re
import json
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

            def remove_readonly(func, path, excinfo):
                os.chmod(path, 0o777)
                func(path)

            await loop.run_in_executor(None, lambda: shutil.rmtree(self.path, onerror=remove_readonly))
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
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"Unexpected error during clone: {str(e)}\n{error_details}")
                await workspace.cleanup()
                raise LoomError(f"Repository clone failed: {str(e) or type(e).__name__}", status_code=500)
            raise

    async def get_current_commit_sha(self, workspace: Workspace) -> str:
        """
        Returns the current commit SHA of the repository in the workspace.
        """
        cmd = ["git", "rev-parse", "HEAD"]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise LoomError(f"Failed to get commit SHA: {stderr.decode().strip()}")
            return stdout.decode().strip()
        except Exception as e:
            logger.error(f"Error getting commit SHA: {str(e)}")
            raise LoomError(f"Failed to get commit SHA: {str(e)}")

    async def create_contribution_branch(self, workspace: Workspace, branch_name: str):
        """
        Creates and checks out a new branch in the workspace.
        Ensures we start from the default branch.
        """
        try:
            # 1. Create and switch to the new branch
            cmd = ["git", "checkout", "-b", branch_name]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Git checkout failed: {error_msg}")
                raise LoomError(f"Failed to create branch: {error_msg}", status_code=500)

            logger.info(f"Created and checked out branch {branch_name} in {workspace.path}")

        except Exception as e:
            if not isinstance(e, LoomError):
                logger.error(f"Unexpected error creating branch: {str(e)}")
                raise LoomError(f"Branch creation failed: {str(e)}", status_code=500)
            raise

    async def push_contribution(self, workspace: Workspace, branch_name: str, access_token: str, repo_url: str):
        """
        Pushes the contribution branch to the remote GitHub repository.
        """
        try:
            # 1. Verify we are on the correct branch and it exists
            cmd = ["git", "rev-parse", "--abbrev-ref", "HEAD"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            current_branch = stdout.decode().strip()

            if current_branch != branch_name:
                raise LoomError(f"Workspace is on branch {current_branch}, expected {branch_name}")

            # 2. Setup authenticated remote URL for push
            authenticated_url = repo_url.replace("https://", f"https://{access_token}@")

            # 3. Commit changes (if not already committed)
            # We assume implementation agent already added files, but let's be sure
            await asyncio.create_subprocess_exec("git", "add", ".", cwd=str(workspace.path))
            commit_process = await asyncio.create_subprocess_exec(
                "git", "commit", "-m", f"Loom: Implementation for {branch_name}",
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await commit_process.communicate() # Ignore if nothing to commit

            # 4. Push to remote
            # We use -u to track and --force if necessary (but usually not for new AI branches)
            cmd = ["git", "push", authenticated_url, branch_name]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"Git push failed: {error_msg}")

                if "401" in error_msg or "403" in error_msg:
                    raise LoomError("GitHub authentication failed or permission denied during push", status_code=403)
                if "rate limit" in error_msg.lower():
                    raise LoomError("GitHub rate limit exceeded during push", status_code=429)

                raise LoomError(f"Failed to push branch: {error_msg}", status_code=500)

            logger.info(f"Successfully pushed branch {branch_name} to remote.")

        except Exception as e:
            if not isinstance(e, LoomError):
                logger.error(f"Unexpected error during push: {str(e)}")
                raise LoomError(f"Branch push failed: {str(e)}", status_code=500)
            raise

    async def get_contribution_diff(self, workspace: Workspace) -> Dict[str, Any]:
        """
        Generates a git diff for the changes in the workspace.
        """
        try:
            # First, stage all changes so we can see them in diff
            # In a real app we might want more granular control
            subprocess_cmd = ["git", "add", "."]
            process = await asyncio.create_subprocess_exec(
                *subprocess_cmd,
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

            # 1. Get the diff content (staged changes)
            cmd = ["git", "diff", "--staged"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise LoomError(f"Git diff failed: {stderr.decode()}")

            diff_content = stdout.decode("utf-8", errors="replace")

            # 2. Get short stats
            cmd = ["git", "diff", "--staged", "--shortstat"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            stats_text = stdout.decode().strip()

            # 3. Get list of changed files
            cmd = ["git", "diff", "--staged", "--name-only"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(workspace.path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            files = stdout.decode().strip().split("\n")
            files = [f for f in files if f]

            # Parse stats
            additions = 0
            deletions = 0
            if stats_text:
                add_match = re.search(r"(\d+) insertion", stats_text)
                del_match = re.search(r"(\d+) deletion", stats_text)
                additions = int(add_match.group(1)) if add_match else 0
                deletions = int(del_match.group(1)) if del_match else 0

            return {
                "diff": diff_content,
                "stats": stats_text,
                "files": files,
                "additions": additions,
                "deletions": deletions
            }

        except Exception as e:
            logger.error(f"Failed to generate diff: {str(e)}")
            raise LoomError(f"Diff generation failed: {str(e)}", status_code=500)

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

    async def extract_readme_info(self, workspace: Workspace) -> Dict[str, Any]:
        """
        Attempts to find and parse the README file in the workspace.
        Extracts sections like description, installation, usage, etc.
        """
        readme_path = self._find_readme(workspace.path)
        if not readme_path:
            return {
                "found": False,
                "sections": {}
            }

        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()

            return {
                "found": True,
                "file_name": os.path.basename(readme_path),
                "sections": self._parse_readme_sections(content)
            }
        except Exception as e:
            logger.error(f"Failed to read README at {readme_path}: {str(e)}")
            return {"found": False, "error": str(e)}

    def _find_readme(self, base_path: Path) -> Optional[Path]:
        """Finds the most likely README file in the root directory."""
        readme_variants = ["README.md", "README.txt", "README", "readme.md", "ReadMe.md"]
        for variant in readme_variants:
            path = base_path / variant
            if path.exists() and path.is_file():
                return path
        return None

    def _parse_readme_sections(self, content: str) -> Dict[str, str]:
        """
        Simple regex-based parsing of Markdown headers to extract sections.
        """
        sections = {
            "description": "",
            "installation": "",
            "usage": "",
            "architecture": "",
            "development": ""
        }

        # Normalize line endings
        content = content.replace("\r\n", "\n")

        # Basic description: text before the first real header or the first paragraph
        lines = content.split("\n")
        desc_lines = []
        for line in lines:
            if line.startswith("#"):
                if desc_lines: break
                continue
            if line.strip():
                desc_lines.append(line.strip())
            elif desc_lines:
                break
        sections["description"] = " ".join(desc_lines)

        # Map headers to our target sections
        header_mapping = {
            r"install": "installation",
            r"setup": "installation",
            r"getting started": "installation",
            r"usage": "usage",
            r"how to use": "usage",
            r"examples": "usage",
            r"architecture": "architecture",
            r"design": "architecture",
            r"internal": "architecture",
            r"develop": "development",
            r"contributing": "development",
            r"build": "development"
        }

        current_section = None
        section_buffers = {k: [] for k in sections.keys()}

        # Split by headers (Markdown style)
        # Using a simple approach: any line starting with # is a header
        for line in lines:
            if line.startswith("#"):
                header_text = line.lstrip("#").strip().lower()
                current_section = None
                for pattern, target in header_mapping.items():
                    if re.search(pattern, header_text):
                        current_section = target
                        break
            elif current_section:
                section_buffers[current_section].append(line)

        for key in sections.keys():
            if key != "description": # description handled above
                sections[key] = "\n".join(section_buffers[key]).strip()

        return sections

    async def analyze_contribution_rules(self, workspace: Workspace) -> Dict[str, Any]:
        """
        Detects and reads files containing contribution rules,
        including CONTRIBUTING.md and GitHub templates.
        """
        rules = {
            "contributing_guide": None,
            "issue_templates": [],
            "pull_request_templates": []
        }

        # 1. Find and read CONTRIBUTING file
        for variant in settings.CONTRIBUTING_FILE_VARIANTS:
            path = workspace.path / variant
            if path.exists() and path.is_file():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        rules["contributing_guide"] = {
                            "file_name": variant,
                            "content": f.read()
                        }
                    break
                except Exception as e:
                    logger.warning(f"Failed to read {variant}: {str(e)}")

        # 2. Look for GitHub templates (.github directory)
        github_path = workspace.path / settings.GITHUB_DIR
        if github_path.exists() and github_path.is_dir():
            # Issue templates
            for it_dir in settings.ISSUE_TEMPLATE_DIRS:
                it_path = github_path / it_dir
                if it_path.exists() and it_dir:
                    for root, _, files in os.walk(it_path):
                        for file in files:
                            if file.endswith((".md", ".yml", ".yaml")):
                                try:
                                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                                        rules["issue_templates"].append({
                                            "name": file,
                                            "content": f.read()
                                        })
                                except Exception:
                                    pass

            # PR templates
            for variant in settings.PULL_REQUEST_TEMPLATE_VARIANTS:
                pr_path = github_path / variant
                if pr_path.exists() and pr_path.is_file():
                    try:
                        with open(pr_path, "r", encoding="utf-8") as f:
                            rules["pull_request_templates"].append({
                                "name": variant,
                                "content": f.read()
                            })
                    except Exception:
                        pass

        # Also check root for PR template
        if not rules["pull_request_templates"]:
             for variant in settings.PULL_REQUEST_TEMPLATE_VARIANTS:
                pr_path = workspace.path / variant
                if pr_path.exists() and pr_path.is_file():
                    try:
                        with open(pr_path, "r", encoding="utf-8") as f:
                            rules["pull_request_templates"].append({
                                "name": variant,
                                "content": f.read()
                            })
                    except Exception:
                        pass

        return rules

    async def detect_build_system(self, workspace: Workspace) -> Dict[str, Any]:
        """
        Detects the build system and primary language markers of a repository.
        """
        path = workspace.path
        info = {
            "systems": [],
            "primary_language": None,
            "has_lock_file": False,
            "has_wrapper": False
        }

        # Build system markers mapping
        markers = {
            "npm": ["package.json"],
            "yarn": ["yarn.lock"],
            "pnpm": ["pnpm-lock.yaml"],
            "gradle": ["build.gradle", "build.gradle.kts", "settings.gradle"],
            "maven": ["pom.xml"],
            "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "go": ["go.mod"],
            "rust": ["Cargo.toml"],
            "make": ["Makefile"],
            "cmake": ["CMakeLists.txt"]
        }

        # Detection logic
        for system, files in markers.items():
            for file in files:
                if (path / file).exists():
                    if system not in info["systems"]:
                        info["systems"].append(system)

                    # Language inference
                    if system in ["npm", "yarn", "pnpm"]:
                        info["primary_language"] = "JavaScript/TypeScript"
                    elif system in ["gradle", "maven"]:
                        info["primary_language"] = "Java/Kotlin"
                    elif system == "python":
                        info["primary_language"] = "Python"
                    elif system == "go":
                        info["primary_language"] = "Go"
                    elif system == "rust":
                        info["primary_language"] = "Rust"

        # Check for wrappers
        info["has_wrapper"] = (path / "gradlew").exists() or (path / "mvnw").exists()

        # Check for lock files
        lock_files = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock", "go.sum"]
        info["has_lock_file"] = any((path / f).exists() for f in lock_files)

        return info

    async def detect_test_system(self, workspace: Workspace, build_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects the test framework and likely test commands based on the structure and build system.
        """
        path = workspace.path
        test_info = {
            "frameworks": [],
            "test_commands": []
        }

        # 1. Node.js Ecosystem
        if any(s in build_info["systems"] for s in ["npm", "yarn", "pnpm"]):
            # Check package.json for test scripts and dependencies
            package_json_path = path / "package.json"
            if package_json_path.exists():
                try:
                    with open(package_json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                        # Framework detection
                        if "jest" in deps or (path / "jest.config.js").exists() or (path / "jest.config.ts").exists():
                            test_info["frameworks"].append("jest")
                        if "mocha" in deps:
                            test_info["frameworks"].append("mocha")
                        if "vitest" in deps or (path / "vitest.config.ts").exists():
                            test_info["frameworks"].append("vitest")
                        if "cypress" in deps:
                            test_info["frameworks"].append("cypress")
                        if "playwright" in deps:
                            test_info["frameworks"].append("playwright")

                        # Command detection
                        if "scripts" in data and "test" in data["scripts"]:
                            manager = "npm"
                            if "yarn" in build_info["systems"]: manager = "yarn"
                            elif "pnpm" in build_info["systems"]: manager = "pnpm"
                            test_info["test_commands"].append(f"{manager} test")
                except Exception:
                    pass

        # 2. Python Ecosystem
        if "python" in build_info["systems"]:
            if (path / "pytest.ini").exists() or (path / "conftest.py").exists() or (path / "tests").exists():
                test_info["frameworks"].append("pytest")
                test_info["test_commands"].append("pytest")
            elif (path / "tox.ini").exists():
                test_info["frameworks"].append("tox")
                test_info["test_commands"].append("tox")
            else:
                test_info["frameworks"].append("unittest")
                test_info["test_commands"].append("python -m unittest discover")

        # 3. Java/Kotlin Ecosystem
        if "gradle" in build_info["systems"]:
            test_info["frameworks"].append("junit") # Assume JUnit for JVM
            cmd = "./gradlew test" if build_info["has_wrapper"] else "gradle test"
            test_info["test_commands"].append(cmd)
        elif "maven" in build_info["systems"]:
            test_info["frameworks"].append("junit")
            cmd = "./mvnw test" if build_info["has_wrapper"] else "mvn test"
            test_info["test_commands"].append(cmd)

        # 4. Go Ecosystem
        if "go" in build_info["systems"]:
            test_info["frameworks"].append("go test")
            test_info["test_commands"].append("go test ./...")

        # 5. Rust Ecosystem
        if "rust" in build_info["systems"]:
            test_info["frameworks"].append("cargo test")
            test_info["test_commands"].append("cargo test")

        return test_info

    async def detect_code_signals(self, workspace: Workspace) -> List[Dict[str, Any]]:
        """
        Scans the workspace for code-level signals like TODO, FIXME,
        and unimplemented markers.
        """
        signals = []
        path = workspace.path

        # Regex patterns for common signals
        patterns = {
            "TODO": re.compile(r"TODO[:\s]+(.+)", re.IGNORECASE),
            "FIXME": re.compile(r"FIXME[:\s]+(.+)", re.IGNORECASE),
            "UNIMPLEMENTED": re.compile(r"(pass|NotImplementedError|throw new Error\(.*not implemented.*\))", re.IGNORECASE)
        }

        # Extensions to scan
        valid_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".kt"}

        for root, dirs, files in os.walk(path):
            # Skip ignored dirs
            dirs[:] = [d for d in dirs if d not in settings.IGNORED_DIRECTORIES]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in valid_extensions:
                    continue

                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, path).replace("\\", "/")

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            for signal_type, pattern in patterns.items():
                                match = pattern.search(line)
                                if match:
                                    signals.append({
                                        "type": signal_type,
                                        "path": rel_path,
                                        "line": i,
                                        "content": match.group(0).strip(),
                                        "message": match.group(1).strip() if signal_type != "UNIMPLEMENTED" else ""
                                    })
                except Exception as e:
                    logger.warning(f"Failed to scan file {rel_path} for signals: {str(e)}")

        return signals

    async def detect_test_gaps(self, workspace: Workspace, files_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Heuristically identifies potential test gaps by checking if source files
        have corresponding test files.
        """
        gaps = []
        source_files = []
        test_files = set()

        for f in files_metadata:
            if f["type"] != "file": continue
            path = f["path"].lower()

            # Identify test files
            if "test" in path or "_spec" in path:
                test_files.add(f["path"])
            # Identify source files (in common src dirs)
            elif any(d in path for d in ["src/", "lib/", "app/"]) and f["extension"] in [".py", ".js", ".ts", ".tsx", ".go"]:
                source_files.append(f)

        for src in source_files:
            # Simple heuristic: look for test file with same name or in tests/ mirror
            src_name = os.path.splitext(os.path.basename(src["path"]))[0]

            found = False
            for test in test_files:
                if src_name in test.lower():
                    found = True
                    break

            if not found:
                gaps.append({
                    "type": "test_gap",
                    "path": src["path"],
                    "message": f"No obvious test file found for {os.path.basename(src['path'])}"
                })

        return gaps

repository_service = RepositoryService()
