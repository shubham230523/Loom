import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.agents.opportunity_generator import OpportunityGeneratorAgent, OpportunityProposal, OpportunityList
from backend.app.database.models import Repository, RepositoryIndex, Issue

def test_validate_confidence():
    # Coercion from strings
    assert OpportunityProposal.validate_confidence("high") == 0.9
    assert OpportunityProposal.validate_confidence("Medium") == 0.6
    assert OpportunityProposal.validate_confidence("low risk") == 0.3
    assert OpportunityProposal.validate_confidence("85%") == 0.85
    assert OpportunityProposal.validate_confidence("0.7") == 0.7
    assert OpportunityProposal.validate_confidence("invalid") == 0.5
    # Direct float/int
    assert OpportunityProposal.validate_confidence(0.95) == 0.95
    assert OpportunityProposal.validate_confidence(None) == 0.5

@pytest.mark.asyncio
async def test_generate_opportunities_success():
    agent = OpportunityGeneratorAgent()
    db = AsyncMock()
    repo = Repository(full_name="o/r")
    index = RepositoryIndex(summary={"architecture_summary": "Arch"})

    mock_opp = OpportunityProposal(
        title="T", description="D", type="bug", impact="H", difficulty="E",
        confidence=0.9, evidence_source="S", affected_files=[]
    )
    mock_list = OpportunityList(opportunities=[mock_opp])

    with patch("backend.app.agents.opportunity_generator.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.chat_structured.return_value = mock_list

        res = await agent.generate_opportunities(
            db, repo, index,
            issues=[Issue(number=1, title="I")],
            code_signals=[{"type": "TODO", "path": "f.py", "line": 1, "content": "c"}],
            test_gaps=[{"path": "g.py", "message": "m"}],
            existing_prs=[{"number": 2, "title": "P"}]
        )

        assert len(res) == 1
        assert res[0].title == "T"

@pytest.mark.asyncio
async def test_generate_opportunities_empty_ai_result():
    agent = OpportunityGeneratorAgent()
    db = AsyncMock()
    repo = Repository(full_name="o/r")
    index = RepositoryIndex(summary={})

    with patch("backend.app.agents.opportunity_generator.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.chat_structured.return_value = OpportunityList(opportunities=[])
        res = await agent.generate_opportunities(db, repo, index, [], [], [], [])
        assert res == []

@pytest.mark.asyncio
async def test_generate_opportunities_ai_error():
    agent = OpportunityGeneratorAgent()
    db = AsyncMock()
    repo = Repository(full_name="o/r")
    index = RepositoryIndex(summary={})

    with patch("backend.app.agents.opportunity_generator.ai_gateway", new_callable=AsyncMock) as mock_ai:
        mock_ai.chat_structured.side_effect = Exception("AI Fail")
        with pytest.raises(Exception):
            await agent.generate_opportunities(db, repo, index, [], [], [], [])
