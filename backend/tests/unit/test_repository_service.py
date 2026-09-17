import pytest
import os
import shutil
import asyncio
import subprocess
import json
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.repository.service import RepositoryService, Workspace
from backend.app.config import settings
from backend.app.api.errors import LoomError

@pytest.fixture
def repo_service():
    return RepositoryService()

@pytest.fixture
async def temp_workspace(tmp_path):
    ws = Workspace(workspace_id="test_ws")
    ws.path = tmp_path
    return ws

@pytest.mark.asyncio
async def test_workspace_create_cleanup(tmp_path):
    ws = Workspace(workspace_id="new_ws")
    ws.path = tmp_path / "new_ws"
    await ws.create()
    assert ws.path.exists()
    (ws.path / "test.txt").write_text("hello")
    await ws.cleanup()
    assert not ws.path.exists()

@pytest.mark.asyncio
async def test_run_git_command_fallback(repo_service, tmp_path):
    with patch("asyncio.create_subprocess_exec", side_effect=NotImplementedError):
        with patch("subprocess.Popen") as mock_popen:
            mock_p = MagicMock()
            mock_p.communicate.return_value = ("sync-out", "sync-err")
            mock_p.returncode = 0
            mock_popen.return_value = mock_p
            rc, out, err = await repo_service._run_git_command(["git", "status"], cwd=tmp_path)
            assert rc == 0
            assert out == "sync-out"

@pytest.mark.asyncio
async def test_clone_repository_failures(repo_service, temp_workspace):
    with patch.object(repo_service, "_run_git_command", new_callable=AsyncMock) as mock_run, \
         patch.object(temp_workspace, "create", new_callable=AsyncMock), \
         patch.object(temp_workspace, "cleanup", new_callable=AsyncMock):
        mock_run.return_value = (1, "", "Clone error")
        with pytest.raises(LoomError, match="Failed to clone"):
            await repo_service.clone_repository("http://repo", "token", temp_workspace)
        mock_run.return_value = (0, "", "")
        with patch.object(temp_workspace, "get_size_mb", return_value=settings.MAX_REPO_SIZE_MB + 1):
            with pytest.raises(LoomError, match="Repository too large"):
                await repo_service.clone_repository("http://repo", "token", temp_workspace)
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            with pytest.raises(LoomError, match="clone timed out"):
                await repo_service.clone_repository("http://repo", "token", temp_workspace)

@pytest.mark.asyncio
async def test_push_contribution_full(repo_service, temp_workspace):
    with patch.object(repo_service, "_run_git_command", new_callable=AsyncMock) as mock_run:
        # Success path
        mock_run.side_effect = [
            (0, "feature", ""), (0, "", ""), (0, "", ""), (0, "", "")
        ]
        await repo_service.push_contribution(temp_workspace, "feature", "tok", "https://github.com/o/r")

        # Wrong branch
        mock_run.side_effect = None
        mock_run.return_value = (0, "main", "")
        with pytest.raises(LoomError, match="Workspace is on branch main"):
            await repo_service.push_contribution(temp_workspace, "feature", "tok", "https://github.com/o/r")

@pytest.mark.asyncio
async def test_detect_build_systems_all(repo_service, temp_workspace):
    systems = [
        ("pom.xml", "maven"), ("build.gradle", "gradle"), ("go.mod", "go"),
        ("Cargo.toml", "rust"), ("requirements.txt", "python"), ("Makefile", "make"),
        ("CMakeLists.txt", "cmake"), ("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn")
    ]
    for filename, expected in systems:
        file_path = temp_workspace.path / filename
        file_path.write_text("")
        info = await repo_service.detect_build_system(temp_workspace)
        assert expected in info["systems"]
        file_path.unlink()

@pytest.mark.asyncio
async def test_detect_test_systems_full(repo_service, temp_workspace):
    # Node variants
    build_info = {"systems": ["npm"]}
    (temp_workspace.path / "package.json").write_text(json.dumps({"devDependencies": {"jest": "1"}, "scripts": {"test": "npm test"}}))
    test_info = await repo_service.detect_test_system(temp_workspace, build_info)
    assert "jest" in test_info["frameworks"]

    (temp_workspace.path / "package.json").write_text(json.dumps({"devDependencies": {"mocha": "1"}}))
    test_info = await repo_service.detect_test_system(temp_workspace, build_info)
    assert "mocha" in test_info["frameworks"]

    # Python tox
    build_info = {"systems": ["python"]}
    (temp_workspace.path / "tox.ini").write_text("")
    test_info = await repo_service.detect_test_system(temp_workspace, build_info)
    assert "tox" in test_info["frameworks"]

    # Maven/Gradle
    build_info = {"systems": ["maven"], "has_wrapper": True}
    test_info = await repo_service.detect_test_system(temp_workspace, build_info)
    assert "./mvnw test" in test_info["test_commands"]

@pytest.mark.asyncio
async def test_discover_files_stat_fail(repo_service, temp_workspace):
    (temp_workspace.path / "fail.py").write_text("test")
    with patch("os.stat", side_effect=OSError("fail")):
        discovered = await repo_service.discover_files(temp_workspace)
        assert len([f for f in discovered if f["type"] == "file"]) == 0

@pytest.mark.asyncio
async def test_extract_readme_info_missing(repo_service, temp_workspace):
    info = await repo_service.extract_readme_info(temp_workspace)
    assert info["found"] is False

@pytest.mark.asyncio
async def test_get_contribution_diff_success(repo_service, temp_workspace):
    with patch.object(repo_service, "_run_git_command", new_callable=AsyncMock) as mock_run:
        mock_run.side_effect = [
            (0, "", ""), # add
            (0, "diff content", ""), # diff
            (0, "1 file changed, 1 insertion(+), 1 deletion(-)", ""), # shortstat
            (0, "file.py", "") # name-only
        ]
        diff = await repo_service.get_contribution_diff(temp_workspace)
        assert diff["additions"] == 1
        assert diff["deletions"] == 1

@pytest.mark.asyncio
async def test_workspace_get_size_mb(tmp_path):
    ws = Workspace(workspace_id="size_ws")
    ws.path = tmp_path / "size_ws"
    await ws.create()
    (ws.path / "file1.txt").write_text("a" * 1024 * 1024) # 1MB
    assert ws.get_size_mb() >= 1.0
    await ws.cleanup()

@pytest.mark.asyncio
async def test_get_current_commit_sha(repo_service, temp_workspace):
    with patch.object(repo_service, "_run_git_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "abc123sha", "")
        sha = await repo_service.get_current_commit_sha(temp_workspace)
        assert sha == "abc123sha"

        mock_run.return_value = (1, "", "rev-parse failed")
        with pytest.raises(LoomError):
            await repo_service.get_current_commit_sha(temp_workspace)

@pytest.mark.asyncio
async def test_create_contribution_branch(repo_service, temp_workspace):
    with patch.object(repo_service, "_run_git_command", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (0, "", "")
        await repo_service.create_contribution_branch(temp_workspace, "new-feature")

        mock_run.return_value = (1, "", "branch exists")
        with pytest.raises(LoomError):
            await repo_service.create_contribution_branch(temp_workspace, "new-feature")

@pytest.mark.asyncio
async def test_push_contribution_ssh_and_errors(repo_service, temp_workspace):
    with patch.object(repo_service, "_run_git_command", new_callable=AsyncMock) as mock_run:
        # SSH URL conversion
        mock_run.side_effect = [
            (0, "feature", ""), (0, "", ""), (0, "", ""), (0, "", "")
        ]
        await repo_service.push_contribution(temp_workspace, "feature", "tok", "git@github.com:o/r")
        # Check if URL was correctly handled in the last call (push)
        last_call_args = mock_run.call_args_list[-1][0][0]
        assert "https://x-access-token:tok@github.com/o/r.git" in last_call_args

        # Auth failure
        mock_run.side_effect = None
        mock_run.side_effect = [(0, "feature", ""), (0, "", ""), (0, "", ""), (1, "", "403 Forbidden")]
        with pytest.raises(LoomError, match="GitHub authentication failed"):
            await repo_service.push_contribution(temp_workspace, "feature", "tok", "https://github.com/o/r")

@pytest.mark.asyncio
async def test_discover_files_not_exist_and_dirs(repo_service, tmp_path):
    ws = Workspace(workspace_id="nonexistent")
    ws.path = tmp_path / "void"
    with pytest.raises(LoomError, match="Workspace path does not exist"):
        await repo_service.discover_files(ws)

    await ws.create()
    os.makedirs(ws.path / "subdir")
    discovered = await repo_service.discover_files(ws)
    assert any(d["type"] == "directory" and d["name"] == "subdir" for d in discovered)

@pytest.mark.asyncio
async def test_extract_readme_parsing(repo_service, temp_workspace):
    readme_content = """
# Loom
A great tool.

## Installation
Run pip install.

## Usage
Click buttons.
"""
    (temp_workspace.path / "README.md").write_text(readme_content)
    info = await repo_service.extract_readme_info(temp_workspace)
    assert info["found"] is True
    assert info["sections"]["description"] == "A great tool."
    assert "Run pip install." in info["sections"]["installation"]
    assert "Click buttons." in info["sections"]["usage"]

@pytest.mark.asyncio
async def test_analyze_contribution_rules_templates(repo_service, temp_workspace):
    dot_github = temp_workspace.path / ".github"
    dot_github.mkdir()
    # On Windows, "pull_request_template.md" and "PULL_REQUEST_TEMPLATE.md" are the same file.
    # We just create one.
    (dot_github / "pull_request_template.md").write_text("PR Template")

    it_dir = dot_github / "ISSUE_TEMPLATE"
    it_dir.mkdir()
    (it_dir / "bug.md").write_text("Bug Template")

    rules = await repo_service.analyze_contribution_rules(temp_workspace)
    # Use >= because Windows filesystem might cause multiple matches if variants differ only by case
    assert len(rules["pull_request_templates"]) >= 1
    assert rules["pull_request_templates"][0]["content"] == "PR Template"
    assert len(rules["issue_templates"]) >= 1
    assert rules["issue_templates"][0]["content"] == "Bug Template"

@pytest.mark.asyncio
async def test_detect_code_signals(repo_service, temp_workspace):
    code = """
    # TODO: Implement this
    def foo():
        pass # FIXME: Fix this
        # UNIMPLEMENTED
        raise NotImplementedError("Not done")
    """
    (temp_workspace.path / "foo.py").write_text(code)
    signals = await repo_service.detect_code_signals(temp_workspace)
    types = [s["type"] for s in signals]
    assert "TODO" in types
    assert "FIXME" in types
    assert "UNIMPLEMENTED" in types

@pytest.mark.asyncio
async def test_detect_test_systems_edge_cases(repo_service, temp_workspace):
    # Gradle without wrapper
    (temp_workspace.path / "build.gradle").write_text("")
    info = await repo_service.detect_build_system(temp_workspace)
    assert "gradle" in info["systems"]
    test_info = await repo_service.detect_test_system(temp_workspace, info)
    assert "gradle test" in test_info["test_commands"]
    (temp_workspace.path / "build.gradle").unlink()

    # package.json without specialized frameworks
    (temp_workspace.path / "package.json").write_text(json.dumps({"scripts": {"test": "echo 'no real test'"}}))
    info = {"systems": ["npm"]}
    test_info = await repo_service.detect_test_system(temp_workspace, info)
    assert "npm test" in test_info["test_commands"]

@pytest.mark.asyncio
async def test_extract_readme_txt(repo_service, temp_workspace):
    (temp_workspace.path / "README.txt").write_text("# Title\n\nDescription here.")
    info = await repo_service.extract_readme_info(temp_workspace)
    assert info["found"] is True
    assert "Description here" in info["sections"]["description"]

@pytest.mark.asyncio
async def test_extract_readme_error(repo_service, temp_workspace):
    (temp_workspace.path / "README.md").write_text("data")
    with patch("builtins.open", side_effect=Exception("Read fail")):
        info = await repo_service.extract_readme_info(temp_workspace)
        assert info["found"] is False
        assert "error" in info

@pytest.mark.asyncio
async def test_detect_test_systems_all_branches(repo_service, temp_workspace):
    # Test all branches in detect_test_system
    # 1. npm test scripts
    (temp_workspace.path / "package.json").write_text(json.dumps({"scripts": {"test": "npm test"}}))
    info = {"systems": ["npm"]}
    test_info = await repo_service.detect_test_system(temp_workspace, info)
    assert "npm test" in test_info["test_commands"]

    # 2. yarn
    info = {"systems": ["yarn"]}
    test_info = await repo_service.detect_test_system(temp_workspace, info)
    assert "yarn test" in test_info["test_commands"]

    # 3. pnpm
    info = {"systems": ["pnpm"]}
    test_info = await repo_service.detect_test_system(temp_workspace, info)
    assert "pnpm test" in test_info["test_commands"]

    # 4. python pytest folders
    (temp_workspace.path / "tests").mkdir(exist_ok=True)
    info = {"systems": ["python"]}
    test_info = await repo_service.detect_test_system(temp_workspace, info)
    assert "pytest" in test_info["frameworks"]

@pytest.mark.asyncio
async def test_detect_test_gaps_more(repo_service, temp_workspace):
    metadata = [
        {"path": "src/main.go", "type": "file", "extension": ".go"},
        {"path": "src/api.ts", "type": "file", "extension": ".ts"},
        {"path": "src/logic.js", "type": "file", "extension": ".js"},
        {"path": "app/core.py", "type": "file", "extension": ".py"}
    ]
    gaps = await repo_service.detect_test_gaps(temp_workspace, metadata)
    assert len(gaps) == 4

@pytest.mark.asyncio
async def test_detect_code_signals_languages(repo_service, temp_workspace):
    (temp_workspace.path / "test.js").write_text("// TODO: js todo")
    (temp_workspace.path / "test.ts").write_text("// FIXME: ts fixme")
    signals = await repo_service.detect_code_signals(temp_workspace)
    assert any(s["type"] == "TODO" for s in signals)
    assert any(s["type"] == "FIXME" for s in signals)

def test_find_readme_variants(repo_service, tmp_path):
    # Test README.txt
    (tmp_path / "README.txt").write_text("content")
    assert repo_service._find_readme(tmp_path).name == "README.txt"
    (tmp_path / "README.txt").unlink()

    # Test README (no extension)
    (tmp_path / "README").write_text("content")
    assert repo_service._find_readme(tmp_path).name == "README"
    (tmp_path / "README").unlink()

    assert repo_service._find_readme(tmp_path) is None

@pytest.mark.asyncio
async def test_detect_test_systems_extra(repo_service, temp_workspace):
    # Maven without wrapper
    (temp_workspace.path / "pom.xml").write_text("")
    info = {"systems": ["maven"], "has_wrapper": False}
    test_info = await repo_service.detect_test_system(temp_workspace, info)
    assert "mvn test" in test_info["test_commands"]

    # Gradle with wrapper
    (temp_workspace.path / "build.gradle").write_text("")
    info = {"systems": ["gradle"], "has_wrapper": True}
    test_info = await repo_service.detect_test_system(temp_workspace, info)
    assert "./gradlew test" in test_info["test_commands"]

    # Vitest
    (temp_workspace.path / "package.json").write_text(json.dumps({"devDependencies": {"vitest": "1"}}))
    info = {"systems": ["npm"]}
    test_info = await repo_service.detect_test_system(temp_workspace, info)
    assert "vitest" in test_info["frameworks"]

@pytest.mark.asyncio
async def test_detect_code_signals_empty(repo_service, temp_workspace):
    # Test with no files
    signals = await repo_service.detect_code_signals(temp_workspace)
    assert signals == []
