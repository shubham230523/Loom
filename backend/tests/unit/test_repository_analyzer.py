import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.repository.analyzer import RepositoryAnalyzer, RepositorySummary

@pytest.fixture
def analyzer():
    return RepositoryAnalyzer()

@pytest.mark.asyncio
async def test_generate_summary_success(analyzer):
    workspace = MagicMock()
    build_info = {"systems": ["npm"], "primary_language": "TS"}
    test_info = {"frameworks": ["jest"]}
    readme_info = {"found": True, "sections": {"description": "desc"}}
    files_metadata = [{"path": "src/main.ts"}]

    mock_summary = RepositorySummary(
        architecture_summary="Arch",
        important_modules=["src"],
        technology_summary="Tech",
        development_workflow="Dev",
        testing_workflow="Test"
    )

    with patch("backend.app.repository.analyzer.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.chat_structured.return_value = mock_summary

        summary = await analyzer.generate_summary(workspace, build_info, test_info, readme_info, files_metadata)

        assert summary.architecture_summary == "Arch"
        assert "src" in summary.important_modules
        mock_ai.chat_structured.assert_called_once()

@pytest.mark.asyncio
async def test_update_index_summary(analyzer):
    db = AsyncMock()
    index = MagicMock(id="idx")
    workspace = MagicMock()

    with patch("backend.app.repository.analyzer.repository_service", new_callable=AsyncMock) as mock_repo_svc, \
         patch.object(analyzer, "generate_summary", new_callable=AsyncMock) as mock_gen_sum, \
         patch("backend.app.repository.analyzer.embedding_service", new_callable=AsyncMock):

        mock_repo_svc.detect_build_system.return_value = {}
        mock_repo_svc.detect_test_system.return_value = {}
        mock_repo_svc.extract_readme_info.return_value = {}
        mock_repo_svc.discover_files.return_value = []

        mock_gen_sum.return_value = MagicMock(model_dump=lambda: {"arch": "test"})

        await analyzer.update_index_summary(db, index, workspace)

        assert index.summary == {"arch": "test"}
