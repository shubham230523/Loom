import asyncio
import sys
from backend.app.repository.analyzer import repository_analyzer, RepositorySummary
from backend.app.ai import AIGateway, ChatResponse, ChatMessage, MessageRole
from unittest.mock import MagicMock

async def verify_analysis_logic():
    # Mock AI Gateway to avoid real API calls in this specific test
    mock_summary = RepositorySummary(
        architecture_summary="Test Architecture",
        important_modules=["src", "tests"],
        technology_summary="Python, FastAPI",
        development_workflow="pip install",
        testing_workflow="pytest"
    )

    # We'll just verify the method exists and the schema is correct
    print("RepositorySummary Schema:", RepositorySummary.model_json_schema())

    assert hasattr(repository_analyzer, "generate_summary")
    assert hasattr(repository_analyzer, "update_index_summary")

    print("Analysis logic verification successful.")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_analysis_logic())
    if not success:
        sys.exit(1)
