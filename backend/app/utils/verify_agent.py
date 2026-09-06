import asyncio
import sys
from backend.app.agents import issue_analyzer_agent, IssueAnalysis
from backend.app.utils.logging import logger

async def verify_agent():
    logger.info("Verifying IssueAnalyzerAgent...")
    assert hasattr(issue_analyzer_agent, "analyze_issue")

    # Check schema
    print("IssueAnalysis Schema:", IssueAnalysis.model_json_schema())

    logger.info("IssueAnalyzerAgent verification successful.")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_agent())
    if not success:
        sys.exit(1)
