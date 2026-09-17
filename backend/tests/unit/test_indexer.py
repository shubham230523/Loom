import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.repository.indexer import RepositoryIndexer
from backend.app.database import Repository, RepositoryIndex

@pytest.fixture
def indexer():
    return RepositoryIndexer()

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.add = MagicMock()
    return db

@pytest.mark.asyncio
async def test_index_repository_success(indexer, mock_db):
    repo = Repository(id="1", owner="o", name="n", html_url="h")

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None # No existing index
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.indexer.Workspace", return_value=AsyncMock()) as mock_ws_class, \
         patch("backend.app.repository.indexer.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.indexer.symbol_extractor", new_callable=AsyncMock), \
         patch("backend.app.repository.indexer.repository_analyzer", new_callable=AsyncMock), \
         patch("backend.app.repository.indexer.embedding_service", new_callable=AsyncMock):

        mock_repo_svc.get_current_commit_sha.return_value = "sha1"
        mock_repo_svc.discover_files.return_value = [{"path": "p", "type": "file", "size_kb": 1}]

        index = await indexer.index_repository(mock_db, repo, "token")

        assert index.status == "completed"
        assert index.commit_sha == "sha1"
        mock_db.commit.assert_called()

@pytest.mark.asyncio
async def test_index_repository_reuse_existing(indexer, mock_db):
    repo = Repository(id="1", owner="o", name="n", html_url="h")
    existing_index = RepositoryIndex(id="old", status="completed")

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_index
    mock_db.execute.return_value = mock_result

    with patch("backend.app.repository.indexer.Workspace", return_value=AsyncMock()), \
         patch("backend.app.repository.indexer.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch("backend.app.repository.indexer.symbol_extractor", new_callable=AsyncMock), \
         patch("backend.app.repository.indexer.repository_analyzer", new_callable=AsyncMock), \
         patch("backend.app.repository.indexer.embedding_service", new_callable=AsyncMock):

        mock_repo_svc.get_current_commit_sha.return_value = "sha1"

        index = await indexer.index_repository(mock_db, repo, "token")

        assert index.id == "old"
        assert index.status == "completed"
