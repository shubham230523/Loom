import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.agents.conflict_detector import ConflictDetectorAgent, ConflictAssessment, json_to_text

def test_json_to_text():
    assert json_to_text(None) == "None found."
    assert json_to_text([]) == "None found."
    import json
    data = {"a": 1}
    assert json_to_text(data) == json.dumps(data, indent=2)

@pytest.mark.asyncio
async def test_assess_opportunity_conflicts_success():
    agent = ConflictDetectorAgent()
    db = AsyncMock()
    repository = MagicMock(id="repo-id", full_name="org/repo")
    client = MagicMock()

    mock_results = [
        {"type": "issue", "score": 0.85, "title": "Dup issue"},
        {"type": "issue", "score": 0.5, "title": "Low score issue"},
        {"type": "file", "score": 0.9, "path": "src/main.py"}
    ]

    mock_assessment = ConflictAssessment(
        risk_level="High",
        duplicate_issues=[{"title": "Dup issue"}],
        conflicting_prs=[],
        reasoning="Duplicate found",
        is_duplicate=True
    )

    with patch("backend.app.agents.conflict_detector.semantic_search_service", new_callable=AsyncMock) as mock_search, \
         patch("backend.app.agents.conflict_detector.pr_service", new_callable=AsyncMock) as mock_pr, \
         patch("backend.app.ai.gateway.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:

        mock_search.search.return_value = mock_results
        mock_pr.detect_conflicts.return_value = []
        mock_pr.get_repository_pull_requests.return_value = [{"number": 1, "title": "PR 1"}]
        mock_chat.return_value = mock_assessment

        res = await agent.assess_opportunity_conflicts(
            db=db,
            repository=repository,
            client=client,
            title="Title",
            description="Desc",
            affected_files=["src/main.py"]
        )

        assert res.risk_level == "High"
        assert res.is_duplicate is True
        mock_search.search.assert_called_once()
        mock_pr.detect_conflicts.assert_called_once_with(repository, client, ["src/main.py"])
        mock_pr.get_repository_pull_requests.assert_called_once_with(repository, client, state="open", limit=30)
        mock_chat.assert_called_once()
