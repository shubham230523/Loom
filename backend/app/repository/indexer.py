from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from backend.app.config import settings
from backend.app.database import Repository, RepositoryIndex, RepositoryFile, RepositorySymbol
from backend.app.repository.service import repository_service, Workspace
from backend.app.repository.symbol_extractor import symbol_extractor
from backend.app.repository.analyzer import repository_analyzer
from backend.app.ai import embedding_service
from backend.app.utils.logging import logger
from backend.app.api.errors import LoomError

class RepositoryIndexer:
    async def index_repository(
        self,
        db: AsyncSession,
        repository: Repository,
        access_token: str,
        branch: str = "main",
        commit_sha: Optional[str] = None
    ) -> RepositoryIndex:
        """
        Clones, analyzes, and indexes a repository.
        Reuses existing index if commit_sha matches.
        """
        logger.info(f"Indexer: Starting indexing for {repository.full_name}")

        # 1. Create a placeholder index record immediately to prevent duplicate tasks
        index = RepositoryIndex(
            repository_id=repository.id,
            branch=branch,
            commit_sha=commit_sha or "unknown",
            status="in_progress"
        )
        db.add(index)
        await db.commit()
        await db.refresh(index)

        workspace = Workspace()
        try:
            # 2. Clone repository
            logger.info(f"Indexer: Cloning {repository.full_name}...")
            await repository_service.clone_repository(
                repo_url=repository.html_url,
                access_token=access_token,
                workspace=workspace
            )

            # 3. Get actual commit SHA
            actual_sha = await repository_service.get_current_commit_sha(workspace)

            # Check if this SHA is already completed elsewhere
            query = select(RepositoryIndex).where(
                RepositoryIndex.repository_id == repository.id,
                RepositoryIndex.commit_sha == actual_sha,
                RepositoryIndex.status == "completed"
            )
            result = await db.execute(query)
            existing_completed = result.scalars().first()

            if existing_completed:
                logger.info(f"Indexer: Found completed index for {actual_sha}, cleaning up placeholder.")
                index.status = "completed" # Or just delete placeholder
                await db.commit()
                return existing_completed

            index.commit_sha = actual_sha
            await db.commit()

            # 4. Discover files
            logger.info(f"Indexer: Discovering files...")
            files_metadata = await repository_service.discover_files(workspace)

            # 6. Extract symbols and persist
            all_files = []
            all_symbols = []

            for file_info in files_metadata:
                if file_info["type"] != "file":
                    continue

                repo_file = RepositoryFile(
                    repository_index_id=index.id,
                    path=file_info["path"],
                    size_kb=file_info["size_kb"]
                )
                db.add(repo_file)
                await db.flush()
                all_files.append(repo_file)

                # Extract symbols
                try:
                    file_path = workspace.path / file_info["path"]
                    # For safety, we only read if it's within a reasonable size
                    # and use errors="ignore" to avoid encoding issues
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        # Limit read size for AST extraction context
                        content = f.read(settings.MAX_FILE_SIZE_KB * 1024)

                    symbols = await symbol_extractor.extract_symbols(file_info["path"], content)

                    for sym in symbols:
                        db_symbol = RepositorySymbol(
                            repository_file_id=repo_file.id,
                            name=sym["name"],
                            type=sym["type"],
                            start_line=sym["start_line"],
                            end_line=sym["end_line"],
                            start_column=sym["start_column"],
                            end_column=sym["end_column"]
                        )
                        db.add(db_symbol)
                        all_symbols.append(db_symbol)
                except Exception as e:
                    logger.warning(f"Failed to process symbols for {file_info['path']}: {str(e)}")

            # 6b. Generate Embeddings for code structure
            logger.info(f"Generating embeddings for {len(all_files)} files and {len(all_symbols)} symbols")
            await embedding_service.embed_files(db, all_files)
            await embedding_service.embed_symbols(db, all_symbols)

            # 7. Generate AI Summary
            await repository_analyzer.update_index_summary(db, index, workspace)

            # 8. Finalize index
            index.status = "completed"
            db.add(index) # Re-ensure it is in the session
            await db.commit()
            logger.info(f"Successfully indexed {repository.full_name} at {index.commit_sha}")
            return index

        except Exception as e:
            logger.error(f"Indexer: Failed during processing: {str(e)}", exc_info=True)
            # Try to mark the index as failed using a fresh state if possible
            try:
                if index:
                    index.status = "failed"
                    index.error_info = str(e)
                    await db.commit()
            except Exception as commit_error:
                logger.error(f"Indexer: Could not save failure status: {str(commit_error)}")
                await db.rollback()

            raise LoomError(f"Indexing failed: {str(e)}", status_code=500)
        finally:
            await workspace.cleanup()

repository_indexer = RepositoryIndexer()
