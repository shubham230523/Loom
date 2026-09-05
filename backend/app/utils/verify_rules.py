import asyncio
import sys
import os
from backend.app.repository import repository_service, Workspace
from backend.app.config import settings
from backend.app.utils.logging import logger

async def verify_rules_logic():
    ws = Workspace(workspace_id="test_verify_rules")
    await ws.create()

    try:
        # 1. Create CONTRIBUTING.md
        with open(ws.path / "CONTRIBUTING.md", "w") as f:
            f.write("# How to contribute\n\nBe nice.")

        # 2. Create .github/ISSUE_TEMPLATE/bug_report.md
        os.makedirs(ws.path / ".github" / "ISSUE_TEMPLATE", exist_ok=True)
        with open(ws.path / ".github" / "ISSUE_TEMPLATE" / "bug_report.md", "w") as f:
            f.write("# Bug Report\n\nDescribe the bug.")

        # 3. Create .github/PULL_REQUEST_TEMPLATE.md
        with open(ws.path / ".github" / "PULL_REQUEST_TEMPLATE.md", "w") as f:
            f.write("# Pull Request\n\nWhat changed?")

        # Analyze rules
        rules = await repository_service.analyze_contribution_rules(ws)

        logger.info(f"Analyzed rules: {rules}")

        assert rules["contributing_guide"] is not None
        assert rules["contributing_guide"]["file_name"] == "CONTRIBUTING.md"
        assert "Be nice" in rules["contributing_guide"]["content"]

        assert len(rules["issue_templates"]) > 0
        assert rules["issue_templates"][0]["name"] == "bug_report.md"

        assert len(rules["pull_request_templates"]) > 0
        assert rules["pull_request_templates"][0]["name"] == "PULL_REQUEST_TEMPLATE.md"

        logger.info("Contribution rules analysis verification successful.")
        return True

    except Exception as e:
        logger.error(f"Contribution rules analysis verification failed: {str(e)}")
        return False
    finally:
        await ws.cleanup()

if __name__ == "__main__":
    if sys.platform == "win32":
        settings.WORKSPACE_BASE_DIR = os.path.join(os.getcwd(), "test_workspaces")

    success = asyncio.run(verify_rules_logic())
    if not success:
        sys.exit(1)
