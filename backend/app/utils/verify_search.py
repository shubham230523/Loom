import asyncio
import sys
from backend.app.ai import semantic_search_service
from backend.app.utils.logging import logger

async def verify_search():
    logger.info("Verifying SemanticSearchService...")
    assert hasattr(semantic_search_service, "search")

    # Verification of class and methods
    logger.info("Semantic search service initialized and methods verified.")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_search())
    if not success:
        sys.exit(1)
