from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.ai.gateway import ai_gateway
from backend.app.ai.schemas import EmbeddingsRequest
from backend.app.database import RepositoryIndex, RepositoryFile, RepositorySymbol, Issue
from backend.app.utils.logging import logger

class EmbeddingService:
    async def embed_repository_index(self, db: AsyncSession, index: RepositoryIndex):
        """Generates embedding for the repository summary/README context."""
        if not index.summary:
            return

        text = f"{index.summary.get('architecture_summary', '')} {index.summary.get('technology_summary', '')}"
        if not text.strip():
            return

        try:
            response = await ai_gateway.generate_embeddings(EmbeddingsRequest(input=text))
            if response.embeddings:
                index.embedding = response.embeddings[0]
                # Committing is handled by the caller
        except Exception as e:
            logger.error(f"Failed to embed repository index {index.id}: {str(e)}")

    async def embed_files(self, db: AsyncSession, files: List[RepositoryFile]):
        """Generates embeddings for file paths and metadata."""
        if not files:
            return

        # Prepare texts: mix of path and name for context
        texts = [f"file: {f.path}" for f in files]

        try:
            # Batch generate if possible (Gateway supports it)
            response = await ai_gateway.generate_embeddings(EmbeddingsRequest(input=texts))

            for i, f in enumerate(files):
                if i < len(response.embeddings):
                    f.embedding = response.embeddings[i]
        except Exception as e:
            logger.error(f"Failed to embed files: {str(e)}")

    async def embed_symbols(self, db: AsyncSession, symbols: List[RepositorySymbol]):
        """Generates embeddings for symbol names and types."""
        if not symbols:
            return

        texts = [f"{s.type}: {s.name}" for s in symbols]

        try:
            # Batch process in chunks of 50 to avoid payload limits
            chunk_size = 50
            for i in range(0, len(texts), chunk_size):
                chunk_texts = texts[i:i + chunk_size]
                chunk_symbols = symbols[i:i + chunk_size]

                response = await ai_gateway.generate_embeddings(EmbeddingsRequest(input=chunk_texts))

                for j, s in enumerate(chunk_symbols):
                    if j < len(response.embeddings):
                        s.embedding = response.embeddings[j]
        except Exception as e:
            logger.error(f"Failed to embed symbols: {str(e)}")

    async def embed_issue(self, db: AsyncSession, issue: Issue):
        """Generates embedding for an issue's title and body."""
        text = f"Issue #{issue.number}: {issue.title}\n\n{issue.body or ''}"
        # Truncate if too long for embedding model
        text = text[:2000]

        try:
            response = await ai_gateway.generate_embeddings(EmbeddingsRequest(input=text))
            if response.embeddings:
                issue.embedding = response.embeddings[0]
        except Exception as e:
            logger.error(f"Failed to embed issue {issue.id}: {str(e)}")

embedding_service = EmbeddingService()
