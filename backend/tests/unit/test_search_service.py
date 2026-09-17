import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.ai.search import SemanticSearchService

@pytest.fixture
def service():
    return SemanticSearchService()

@pytest.mark.asyncio
async def test_search_success(service):
    db = AsyncMock()
    repo_id = uuid.uuid4()

    with patch("backend.app.ai.search.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.generate_embeddings.return_value = MagicMock(embeddings=[[0.1, 0.2]])

        # Mocking complex SQL results
        mock_result = MagicMock()
        mock_result.__iter__.return_value = [] # Empty results for now
        db.execute.return_value = mock_result

        results = await service.search(db, repo_id, "test query")

        assert isinstance(results, list)
        assert db.execute.call_count >= 4 # Symbols, Files, Issues, Indices

@pytest.mark.asyncio
async def test_search_no_embeddings(service):
    db = AsyncMock()
    with patch("backend.app.ai.search.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.generate_embeddings.return_value = MagicMock(embeddings=[])
        results = await service.search(db, uuid.uuid4(), "query")
        assert results == []

@pytest.mark.asyncio
async def test_search_embedding_error(service):
    db = AsyncMock()
    with patch("backend.app.ai.search.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.generate_embeddings.side_effect = Exception("AI Fail")
        results = await service.search(db, uuid.uuid4(), "query")
        assert results == []

@pytest.mark.asyncio
async def test_search_with_results(service):
    db = AsyncMock()
    repo_id = uuid.uuid4()

    with patch("backend.app.ai.search.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.generate_embeddings.return_value = MagicMock(embeddings=[[0.1]])

        sym = MagicMock(name="s", type="f", start_line=1, end_line=2)
        fil = MagicMock(path="p", size_kb=10)
        iss = MagicMock(number=1, title="T", html_url="U")
        idx = MagicMock(summary={"architecture_summary": "Arch"})

        # 1. Symbols, 2. Files, 3. Issues, 4. Indices
        db.execute.side_effect = [
            [(sym, "path/f.py", 0.1)],
            [(fil, 0.2)],
            [(iss, 0.3)],
            [(idx, 0.4)]
        ]

        results = await service.search(db, repo_id, "query")
        assert len(results) == 4
        assert results[0]["type"] == "symbol"
        assert results[0]["score"] == 0.9
