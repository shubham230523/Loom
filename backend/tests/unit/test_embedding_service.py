import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.ai.embeddings import EmbeddingService
from backend.app.database.models import RepositoryIndex, RepositoryFile, RepositorySymbol, Issue

@pytest.fixture
def service():
    return EmbeddingService()

@pytest.mark.asyncio
async def test_embed_repository_index(service):
    db = AsyncMock()
    index = RepositoryIndex(summary={"architecture_summary": "Arch", "technology_summary": "Tech"})

    with patch("backend.app.ai.embeddings.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.generate_embeddings.return_value = MagicMock(embeddings=[[0.1, 0.2]])
        await service.embed_repository_index(db, index)
        assert index.embedding == [0.1, 0.2]

@pytest.mark.asyncio
async def test_embed_files(service):
    db = AsyncMock()
    files = [RepositoryFile(path="f1.py"), RepositoryFile(path="f2.py")]

    with patch("backend.app.ai.embeddings.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.generate_embeddings.return_value = MagicMock(embeddings=[[0.1], [0.2]])
        await service.embed_files(db, files)
        assert files[0].embedding == [0.1]
        assert files[1].embedding == [0.2]

@pytest.mark.asyncio
async def test_embed_symbols(service):
    db = AsyncMock()
    symbols = [RepositorySymbol(name="s1", type="class")]

    with patch("backend.app.ai.embeddings.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.generate_embeddings.return_value = MagicMock(embeddings=[[0.5]])
        await service.embed_symbols(db, symbols)
        assert symbols[0].embedding == [0.5]

@pytest.mark.asyncio
async def test_embed_issue(service):
    db = AsyncMock()
    issue = Issue(number=1, title="T", body="B")

    with patch("backend.app.ai.embeddings.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.generate_embeddings.return_value = MagicMock(embeddings=[[0.9]])
        await service.embed_issue(db, issue)
        assert issue.embedding == [0.9]

@pytest.mark.asyncio
async def test_embed_repository_index_empty(service):
    db = AsyncMock()
    # 1. No summary
    index = RepositoryIndex(summary=None)
    await service.embed_repository_index(db, index)
    assert index.embedding is None

    # 2. Empty summary text
    index.summary = {"architecture_summary": "", "technology_summary": ""}
    await service.embed_repository_index(db, index)
    assert index.embedding is None

@pytest.mark.asyncio
async def test_embed_failures(service):
    db = AsyncMock()
    with patch("backend.app.ai.embeddings.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.generate_embeddings.side_effect = Exception("Fail")

        # Should not raise, just log
        await service.embed_repository_index(db, RepositoryIndex(summary={"a": "b"}))
        await service.embed_files(db, [RepositoryFile(path="f")])
        await service.embed_symbols(db, [RepositorySymbol(name="s")])
        await service.embed_issue(db, Issue(number=1, title="T"))

@pytest.mark.asyncio
async def test_embed_empty_lists(service):
    db = AsyncMock()
    assert await service.embed_files(db, []) is None
    assert await service.embed_symbols(db, []) is None
