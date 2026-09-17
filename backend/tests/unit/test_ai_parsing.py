import pytest
from pydantic import BaseModel
from backend.app.ai.gateway import AIGateway
from backend.app.ai.schemas import ChatRequest, ChatMessage, MessageRole, ChatResponse
from backend.app.api.errors import LoomError

class MockSchema(BaseModel):
    name: str
    score: int

@pytest.mark.asyncio
async def test_chat_structured_success(mocker):
    """Test successful structured output parsing."""
    from unittest.mock import AsyncMock
    mock_provider = mocker.Mock()
    mock_provider.chat_structured = AsyncMock(return_value=MockSchema(name="test", score=100))

    gateway = AIGateway(provider=mock_provider)
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")])

    result = await gateway.chat_structured(request, MockSchema)

    assert isinstance(result, MockSchema)
    assert result.name == "test"
    assert result.score == 100

@pytest.mark.asyncio
async def test_gateway_error_handling(mocker):
    """Verify that gateway normalizes provider errors."""
    mock_provider = mocker.Mock()
    mock_provider.chat.side_effect = Exception("Original error")

    gateway = AIGateway(provider=mock_provider)
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")])

    with pytest.raises(LoomError) as excinfo:
        await gateway.chat(request)

    assert excinfo.value.status_code == 503
    assert "AI service currently unavailable" in excinfo.value.message

def test_opportunity_list_alias_validation():
    """Verify that OpportunityList can handle 'actionable_opportunities' alias."""
    from backend.app.agents.opportunity_generator import OpportunityList

    malformed_json = {
        "status": "no_actionable_signals",
        "repository": "shubham230523/AIMastery",
        "analysis": "Blah blah",
        "actionable_opportunities": []
    }

    # Test dictionary validation
    result = OpportunityList.model_validate(malformed_json)
    assert result.opportunities == []

    # Test with actual opportunities in the alias field
    valid_data = {
        "actionable_opportunities": [
            {
                "title": "Fix something",
                "description": "Details",
                "type": "bug",
                "impact": "High",
                "difficulty": "Easy",
                "confidence": 0.9,
                "evidence_source": "TODO",
                "affected_files": ["main.py"]
            }
        ]
    }
    result2 = OpportunityList.model_validate(valid_data)
    assert len(result2.opportunities) == 1
    assert result2.opportunities[0].title == "Fix something"

def test_opportunity_confidence_coercion():
    """Verify that OpportunityProposal can handle string-based confidence values."""
    from backend.app.agents.opportunity_generator import OpportunityProposal

    base_data = {
        "title": "T", "description": "D", "type": "bug",
        "impact": "H", "difficulty": "E", "evidence_source": "S",
        "affected_files": []
    }

    # Test 'high'
    opp_high = OpportunityProposal.model_validate({**base_data, "confidence": "high"})
    assert opp_high.confidence == 0.9

    # Test 'medium'
    opp_med = OpportunityProposal.model_validate({**base_data, "confidence": "medium"})
    assert opp_med.confidence == 0.6

    # Test percentage string
    opp_pct = OpportunityProposal.model_validate({**base_data, "confidence": "85%"})
    assert opp_pct.confidence == 0.85

    # Test fallback
    opp_fail = OpportunityProposal.model_validate({**base_data, "confidence": "uncertain"})
    assert opp_fail.confidence == 0.5
