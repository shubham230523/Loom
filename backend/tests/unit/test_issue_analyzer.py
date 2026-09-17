import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.agents.issue_analyzer import IssueAnalyzerAgent, IssueAnalysis
from backend.app.database.models import Issue, Repository, RepositoryIndex

@pytest.mark.asyncio
async def test_analyze_issue_success():
    agent = IssueAnalyzerAgent()
    db = AsyncMock()

    repository = Repository(id="repo-id", full_name="org/repo", language="python")
    issue = Issue(number=42, title="Bug title", author="alice", labels=["bug", "high"], body="Crash report")

    mock_index = RepositoryIndex(
        repository_id="repo-id",
        status="completed",
        summary={"architecture_summary": "Arch text", "technology_summary": "Tech text"}
    )

    # Mock database execution for index
    mock_execute_res = MagicMock()
    mock_execute_res.scalars().first.return_value = mock_index
    db.execute.return_value = mock_execute_res

    mock_search_results = [
        {"type": "symbol", "name": "my_func", "symbol_type": "function", "path": "app.py"},
        {"type": "file", "path": "utils.py"}
    ]

    mock_analysis = IssueAnalysis(
        problem_statement="Bug description",
        impact_assessment="High",
        complexity_level="Easy",
        reproducibility="Likely",
        affected_areas=["app.py"],
        is_actionable=True,
        missing_information=None,
        suggested_approach="Fix func"
    )

    with patch("backend.app.agents.issue_analyzer.semantic_search_service", new_callable=AsyncMock) as mock_search, \
         patch("backend.app.ai.gateway.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:

        mock_search.search.return_value = mock_search_results
        mock_chat.return_value = mock_analysis

        res = await agent.analyze_issue(db, issue, repository)

        assert res.problem_statement == "Bug description"
        assert res.is_actionable is True
        mock_search.search.assert_called_once_with(db=db, repository_id="repo-id", query="Bug title", limit=5)
        mock_chat.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_issue_no_index_and_no_search_results():
    agent = IssueAnalyzerAgent()
    db = AsyncMock()

    repository = Repository(id="repo-id", full_name="org/repo", language="python")
    issue = Issue(number=43, title="Title Only", author="bob", labels=None, body=None)

    # No index found
    mock_execute_res = MagicMock()
    mock_execute_res.scalars().first.return_value = None
    db.execute.return_value = mock_execute_res

    mock_analysis = IssueAnalysis(
        problem_statement="Title only",
        impact_assessment="Low",
        complexity_level="Hard",
        reproducibility="Unlikely",
        affected_areas=[],
        is_actionable=False,
        missing_information="Need body",
        suggested_approach=None
    )

    with patch("backend.app.agents.issue_analyzer.semantic_search_service", new_callable=AsyncMock) as mock_search, \
         patch("backend.app.ai.gateway.ai_gateway.chat_structured", new_callable=AsyncMock) as mock_chat:

        mock_search.search.return_value = []
        mock_chat.return_value = mock_analysis

        res = await agent.analyze_issue(db, issue, repository)

        assert res.is_actionable is False
        assert res.missing_information == "Need body"
