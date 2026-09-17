import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel
from backend.app.ai.gateway import AIGateway, LoomError
from backend.app.ai.schemas import (
    ChatRequest, ChatMessage, MessageRole, ChatResponse,
    ChatStreamChunk, EmbeddingsRequest, EmbeddingsResponse
)
from backend.app.config import settings
from backend.app.ai.router import TaskType

@pytest.fixture
def mock_provider():
    return MagicMock() # Use MagicMock for provider to control return types precisely

@pytest.fixture
def gateway(mock_provider):
    return AIGateway(provider=mock_provider)

@pytest.mark.asyncio
async def test_generate_cache_key(gateway):
    req1 = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")], model="m1")
    req2 = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")], model="m1")
    req3 = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="bye")], model="m1")

    key1 = gateway._generate_cache_key(req1, "chat")
    key2 = gateway._generate_cache_key(req2, "chat")
    key3 = gateway._generate_cache_key(req3, "chat")

    assert key1 == key2
    assert key1 != key3

@pytest.mark.asyncio
async def test_chat_cache_hit(gateway):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")], model="m1")
    mock_response = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="hello"),
        usage={"total_tokens": 10}
    )

    settings.ENABLE_AI_CACHE = True

    with patch("backend.app.ai.gateway.redis_service.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response.model_dump_json()

        response = await gateway.chat(request)

        assert response.message.content == "hello"
        gateway._provider.chat.assert_not_called()

@pytest.mark.asyncio
async def test_chat_cache_miss(gateway, mock_provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")], model="m1")
    mock_response = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="hello"),
        usage={"total_tokens": 10}
    )
    mock_provider.chat = AsyncMock(return_value=mock_response)

    settings.ENABLE_AI_CACHE = True

    with patch("backend.app.ai.gateway.redis_service.get", new_callable=AsyncMock) as mock_get, \
         patch("backend.app.ai.gateway.redis_service.set", new_callable=AsyncMock) as mock_set, \
         patch.object(gateway, "_record_run", new_callable=AsyncMock):

        mock_get.return_value = None

        response = await gateway.chat(request, task=TaskType.PLANNING)

        assert response.message.content == "hello"
        mock_provider.chat.assert_called_once()
        mock_set.assert_called_once()

@pytest.mark.asyncio
async def test_chat_error_handling(gateway, mock_provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")], model="m1")
    mock_provider.chat = AsyncMock(side_effect=Exception("API error"))

    settings.ENABLE_AI_CACHE = False

    with patch.object(gateway, "_record_run", new_callable=AsyncMock):
        with pytest.raises(LoomError):
             await gateway.chat(request)

@pytest.mark.asyncio
async def test_chat_stream(gateway, mock_provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")], model="m1")

    async def mock_iter(*args, **kwargs):
        yield ChatStreamChunk(content="h", finish_reason=None)
        yield ChatStreamChunk(content="i", finish_reason="stop")

    mock_provider.chat_stream.side_effect = mock_iter

    with patch.object(gateway, "_record_run", new_callable=AsyncMock):
        chunks = []
        async for chunk in gateway.chat_stream(request):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0].content == "h"

@pytest.mark.asyncio
async def test_chat_stream_error(gateway, mock_provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")], model="m1")

    async def mock_error_iter(*args, **kwargs):
        raise Exception("Stream error")
        yield # Make it a generator

    mock_provider.chat_stream.side_effect = mock_error_iter

    with patch.object(gateway, "_record_run", new_callable=AsyncMock):
        with pytest.raises(LoomError):
            async for _ in gateway.chat_stream(request):
                pass

class MockResponseModel(BaseModel):
    score: int

@pytest.mark.asyncio
async def test_chat_structured_cache_miss(gateway, mock_provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")], model="m1")
    mock_result = MockResponseModel(score=100)
    mock_provider.chat_structured = AsyncMock(return_value=mock_result)

    settings.ENABLE_AI_CACHE = True
    with patch("backend.app.ai.gateway.redis_service.get", new_callable=AsyncMock) as mock_get, \
         patch("backend.app.ai.gateway.redis_service.set", new_callable=AsyncMock) as mock_set, \
         patch.object(gateway, "_record_run", new_callable=AsyncMock):

        mock_get.return_value = None
        res = await gateway.chat_structured(request, MockResponseModel)
        assert res.score == 100
        mock_set.assert_called_once()

@pytest.mark.asyncio
async def test_chat_structured_cache_hit(gateway):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")], model="m1")
    mock_result = MockResponseModel(score=99)

    settings.ENABLE_AI_CACHE = True
    with patch("backend.app.ai.gateway.redis_service.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_result.model_dump_json()
        res = await gateway.chat_structured(request, MockResponseModel)
        assert res.score == 99

@pytest.mark.asyncio
async def test_generate_embeddings_success(gateway, mock_provider):
    request = EmbeddingsRequest(input="test", model="m1")
    mock_resp = EmbeddingsResponse(embeddings=[[0.1, 0.2]], usage={"total_tokens": 5})
    mock_provider.generate_embeddings = AsyncMock(return_value=mock_resp)

    with patch.object(gateway, "_record_run", new_callable=AsyncMock):
        res = await gateway.generate_embeddings(request)
        assert res.embeddings == [[0.1, 0.2]]

@pytest.mark.asyncio
async def test_record_run_success(gateway):
    with patch("backend.app.ai.gateway.SessionLocal") as mock_session_factory:
        mock_db = AsyncMock()
        mock_session_factory.return_value.__aenter__.return_value = mock_db

        await gateway._record_run(model="m1", duration=1.0, status="success", usage={"total_tokens": 10})
        assert mock_db.add.called
        assert mock_db.commit.called

@pytest.mark.asyncio
async def test_record_run_db_error(gateway):
    with patch("backend.app.ai.gateway.SessionLocal", side_effect=Exception("DB down")):
        # Should not raise exception
        await gateway._record_run(model="m1", duration=1.0, status="success")

def test_handle_error_loom_error(gateway):
    le = LoomError("Already loom error")
    with pytest.raises(LoomError) as exc:
        gateway._handle_error(le, "op")
    assert exc.value == le
