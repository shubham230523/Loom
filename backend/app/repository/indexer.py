from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
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
        # 1. Check if index already exists
        if commit_sha:
            query = select(RepositoryIndex).where(
                RepositoryIndex.repository_id == repository.id,
                RepositoryIndex.commit_sha == commit_sha,
                RepositoryIndex.status == "completed"
            )
            result = await db.execute(query)
            existing_index = result.scalar_one_or_none()
            if existing_index:
                logger.info(f"Reusing existing index for {repository.full_name} at {commit_sha}")
                return existing_index

        workspace = Workspace()
        try:
            # 2. Clone repository
            await repository_service.clone_repository(
                repo_url=repository.html_url,
                access_token=access_token,
                workspace=workspace
            )

            # 3. Get actual commit SHA if not provided
            if not commit_sha:
                commit_sha = await repository_service.get_current_commit_sha(workspace)

                # Check again if this SHA is already indexed
                query = select(RepositoryIndex).where(
                    RepositoryIndex.repository_id == repository.id,
                    RepositoryIndex.commit_sha == commit_sha,
                    RepositoryIndex.status == "completed"
                )
                result = await db.execute(query)
                existing_index = result.scalar_one_or_none()
                if existing_index:
                    logger.info(f"Reusing existing index for {repository.full_name} at {commit_sha}")
                    return existing_index

            # 4. Create new index record
            index = RepositoryIndex(
                repository_id=repository.id,
                branch=branch,
                commit_sha=commit_sha,
                status="in_progress"
            )
            db.add(index)
            await db.flush()

            # 5. Discover files
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
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

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
            await db.commit()
            logger.info(f"Successfully indexed {repository.full_name} at {commit_sha}")
            return index

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to index repository: {str(e)}")
            raise LoomError(f"Indexing failed: {str(e)}", status_code=500)
        finally:
            await workspace.cleanup()

repository_indexer = RepositoryIndexer()
