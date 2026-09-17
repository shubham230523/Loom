import pytest
import httpx
import json
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.ai.providers.gemini import GeminiProvider
from backend.app.ai.schemas import ChatRequest, ChatMessage, MessageRole, EmbeddingsRequest
from backend.app.api.errors import LoomError, AuthenticationError, RateLimitError
from pydantic import BaseModel

class SampleResponse(BaseModel):
    answer: str

@pytest.fixture
def provider():
    return GeminiProvider()

def test_gemini_get_url(provider):
    url = provider._get_url("gemini-1.5-pro", "generateContent")
    assert "models/gemini-1.5-pro:generateContent" in url
    assert "key=" in url

def test_gemini_map_messages(provider):
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a bot"),
        ChatMessage(role=MessageRole.USER, content="Hello"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Hi"),
    ]
    mapped = provider._map_messages(messages)
    assert mapped["system_instruction"] == {"parts": [{"text": "You are a bot"}]}
    assert len(mapped["contents"]) == 2
    assert mapped["contents"][0]["role"] == "user"
    assert mapped["contents"][1]["role"] == "model"

@pytest.mark.asyncio
async def test_gemini_chat_success(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": "Hello"}]},
            "finishReason": "STOP"
        }],
        "usageMetadata": {"totalTokenCount": 10}
    }

    request = ChatRequest(
        messages=[ChatMessage(role=MessageRole.USER, content="Hi")],
        response_format={"type": "json_object"}
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = await provider.chat(request)
        assert response.message.content == "Hello"
        assert response.usage["totalTokenCount"] == 10

        # Verify payload contains response_mime_type
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["generationConfig"]["response_mime_type"] == "application/json"

@pytest.mark.asyncio
async def test_gemini_chat_timeout(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(LoomError) as excinfo:
            await provider.chat(request)
        assert excinfo.value.status_code == 504

@pytest.mark.asyncio
async def test_gemini_chat_unexpected_error(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    with patch("httpx.AsyncClient.post", side_effect=ValueError("Unexpected")):
        with pytest.raises(LoomError) as excinfo:
            await provider.chat(request)
        assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test_gemini_handle_error_variants(provider):
    mock_response = MagicMock()

    # 401
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": {"message": "Invalid API Key"}}
    with pytest.raises(AuthenticationError):
        await provider._handle_error(mock_response)

    # 403
    mock_response.status_code = 403
    with pytest.raises(AuthenticationError):
        await provider._handle_error(mock_response)

    # Generic error with no JSON
    mock_response.status_code = 500
    mock_response.json.side_effect = Exception("Not JSON")
    mock_response.text = "Internal Server Error"
    with pytest.raises(LoomError) as excinfo:
        await provider._handle_error(mock_response)
    assert "Internal Server Error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_gemini_chat_stream_success(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])

    mock_response = MagicMock()
    mock_response.status_code = 200

    # Simulate Gemini streaming lines - ensure they are valid JSON after stripping
    chunks = [
        '{"candidates": [{"content": {"parts": [{"text": "Hel"}]}}]}',
        '{"candidates": [{"content": {"parts": [{"text": "lo"}]}}, {"finishReason": "STOP"}]}'
    ]

    mock_response.aiter_lines.return_value = AsyncMockIterator(chunks)

    with patch("httpx.AsyncClient.stream") as mock_stream:
        mock_stream.return_value.__aenter__.return_value = mock_response

        collected = []
        async for chunk in provider.chat_stream(request):
            if chunk.content:
                collected.append(chunk.content)

        assert "".join(collected) == "Hello"

@pytest.mark.asyncio
async def test_gemini_chat_stream_error(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    with patch("httpx.AsyncClient.stream", side_effect=Exception("Stream failed")):
        with pytest.raises(LoomError) as excinfo:
            async for _ in provider.chat_stream(request):
                pass
        assert excinfo.value.status_code == 500

@pytest.mark.asyncio
async def test_gemini_chat_structured_success(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": "{\"answer\": \"42\"}"}]},
            "finishReason": "STOP"
        }]
    }

    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="What is the answer?")])

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await provider.chat_structured(request, SampleResponse)
        assert result.answer == "42"

@pytest.mark.asyncio
async def test_gemini_chat_structured_failure(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{
            "content": {"parts": [{"text": "not json"}]},
            "finishReason": "STOP"
        }]
    }

    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(LoomError) as excinfo:
            await provider.chat_structured(request, SampleResponse)
        assert excinfo.value.status_code == 502

@pytest.mark.asyncio
async def test_gemini_embeddings_success(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embedding": {"values": [0.1, 0.2]}}

    request = EmbeddingsRequest(input=["test1", "test2"])

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = await provider.generate_embeddings(request)
        assert len(response.embeddings) == 2
        assert response.embeddings[0] == [0.1, 0.2]

@pytest.mark.asyncio
async def test_gemini_embeddings_error(provider):
    request = EmbeddingsRequest(input="test")
    with patch("httpx.AsyncClient.post", side_effect=Exception("Embed error")):
        with pytest.raises(LoomError) as excinfo:
            await provider.generate_embeddings(request)
        assert excinfo.value.status_code == 500

class AsyncMockIterator:
    def __init__(self, items):
        self.items = items
    def __aiter__(self):
        return self
    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)
