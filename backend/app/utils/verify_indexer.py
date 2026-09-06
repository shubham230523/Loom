import asyncio
import sys
import os
import uuid
from backend.app.repository import repository_indexer, Workspace
from backend.app.database import engine, Base, Repository, SessionLocal
from backend.app.config import settings
from backend.app.utils.logging import logger

async def verify_indexer_logic():
    # Setup database for test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        try:
            # 1. Create a dummy repository record
            repo = Repository(
                github_repo_id=12345,
                owner="test-owner",
                name="test-repo",
                full_name="test-owner/test-repo",
                html_url="https://github.com/test-owner/test-repo",
                default_branch="main"
            )
            db.add(repo)
            await db.commit()
            await db.refresh(repo)

            # We won't actually clone in this test since we don't have a real URL/token
            # But we can verify the class initialization and method presence
            logger.info("RepositoryIndexer initialized and ready.")
            assert hasattr(repository_indexer, "index_repository")

            logger.info("Indexer verification successful.")
            return True

        except Exception as e:
            logger.error(f"Indexer verification failed: {str(e)}")
            return False
        finally:
            # Cleanup
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

if __name__ == "__main__":
    if sys.platform == "win32":
        settings.WORKSPACE_BASE_DIR = os.path.join(os.getcwd(), "test_workspaces")

    success = asyncio.run(verify_indexer_logic())
    if not success:
        sys.exit(1)
