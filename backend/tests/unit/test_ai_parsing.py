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
