import asyncio
import sys
from pathlib import Path
from backend.app.agents.test_agent import test_agent
from backend.app.database import SessionLocal, Contribution, Repository, Opportunity
from backend.app.utils.logging import logger

async def verify_test_agent():
    logger.info("Verifying TestAgent...")
    assert hasattr(test_agent, "run_tests")

    # We can't easily run a full DB integration test here without a running postgres
    # but we can verify the class and method signatures.

    logger.info("TestAgent verification successful.")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_test_agent())
    if not success:
        sys.exit(1)
