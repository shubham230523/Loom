from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from backend.app.ai.gateway import ai_gateway
from backend.app.ai.schemas import EmbeddingsRequest
from backend.app.database import RepositoryIndex, RepositoryFile, RepositorySymbol, Issue
from backend.app.utils.logging import logger

class SemanticSearchService:
    async def search(
        self,
        db: AsyncSession,
        repository_id: UUID,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Performs a semantic search across files, symbols, and issues.
        Returns ranked results based on cosine similarity.
        """
        # 1. Generate query embedding
        try:
            response = await ai_gateway.generate_embeddings(EmbeddingsRequest(input=query))
            if not response.embeddings:
                return []
            query_vector = response.embeddings[0]
        except Exception as e:
            logger.error(f"Failed to generate embedding for search query: {str(e)}")
            return []

        results = []

        # 2. Search Symbols (Most granular)
        symbol_dist = RepositorySymbol.embedding.cosine_distance(query_vector)
        symbol_query = (
            select(RepositorySymbol, RepositoryFile.path, symbol_dist.label("distance"))
            .join(RepositoryFile)
            .join(RepositoryIndex)
            .where(RepositoryIndex.repository_id == repository_id)
            .order_by(text("distance"))
            .limit(limit)
        )
        symbol_results = await db.execute(symbol_query)
        for sym, path, dist in symbol_results:
            results.append({
                "type": "symbol",
                "name": sym.name,
                "symbol_type": sym.type,
                "path": path,
                "location": {
                    "start_line": sym.start_line,
                    "end_line": sym.end_line
                },
                "score": 1 - dist if dist is not None else 0
            })

        # 3. Search Files
        file_dist = RepositoryFile.embedding.cosine_distance(query_vector)
        file_query = (
            select(RepositoryFile, file_dist.label("distance"))
            .join(RepositoryIndex)
            .where(RepositoryIndex.repository_id == repository_id)
            .order_by(text("distance"))
            .limit(limit)
        )
        file_results = await db.execute(file_query)
        for f, dist in file_results:
            results.append({
                "type": "file",
                "path": f.path,
                "size_kb": f.size_kb,
                "score": 1 - dist if dist is not None else 0
            })

        # 4. Search Issues
        issue_dist = Issue.embedding.cosine_distance(query_vector)
        issue_query = (
            select(Issue, issue_dist.label("distance"))
            .where(Issue.repository_id == repository_id)
            .order_by(text("distance"))
            .limit(limit)
        )
        issue_results = await db.execute(issue_query)
        for iss, dist in issue_results:
            results.append({
                "type": "issue",
                "number": iss.number,
                "title": iss.title,
                "url": iss.html_url,
                "score": 1 - dist if dist is not None else 0
            })

        # 5. Search Repository Summaries
        index_dist = RepositoryIndex.embedding.cosine_distance(query_vector)
        index_query = (
            select(RepositoryIndex, index_dist.label("distance"))
            .where(RepositoryIndex.repository_id == repository_id)
            .order_by(text("distance"))
            .limit(3)
        )
        index_results = await db.execute(index_query)
        for idx, dist in index_results:
            if idx.summary:
                results.append({
                    "type": "documentation",
                    "title": "Architecture Summary",
                    "content": idx.summary.get("architecture_summary", ""),
                    "score": 1 - dist if dist is not None else 0
                })

        # Sort combined results by score descending
        results.sort(key=lambda x: x["score"], reverse=True)

        return results[:limit * 2]

semantic_search_service = SemanticSearchService()
