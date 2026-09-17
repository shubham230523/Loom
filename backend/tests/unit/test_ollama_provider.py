import pytest
import httpx
import json
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.ai.providers.ollama import OllamaCloudProvider
from backend.app.ai.schemas import ChatRequest, ChatMessage, MessageRole, EmbeddingsRequest
from backend.app.api.errors import LoomError, AuthenticationError, RateLimitError
from pydantic import BaseModel

class SampleModel(BaseModel):
    answer: str

@pytest.fixture
def provider():
    return OllamaCloudProvider()

def test_ollama_get_headers(provider):
    headers = provider._get_headers()
    assert headers["Content-Type"] == "application/json"
    if provider.api_key:
        assert "Authorization" in headers

def test_ollama_get_headers_no_key(provider):
    provider.api_key = None
    headers = provider._get_headers()
    assert "Authorization" not in headers

@pytest.mark.asyncio
async def test_ollama_handle_error_variants(provider):
    mock_response = MagicMock()

    # 401
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": "Unauthorized"}
    with pytest.raises(AuthenticationError):
        await provider._handle_error(mock_response)

    # 429
    mock_response.status_code = 429
    with pytest.raises(RateLimitError):
        await provider._handle_error(mock_response)

    # Generic error with no JSON
    mock_response.status_code = 500
    mock_response.json.side_effect = Exception("Not JSON")
    mock_response.text = "Internal Server Error"
    with pytest.raises(LoomError) as excinfo:
        await provider._handle_error(mock_response)
    assert "Internal Server Error" in str(excinfo.value)

@pytest.mark.asyncio
async def test_ollama_chat_success(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"role": "assistant", "content": "Hi there"},
        "done": True,
        "prompt_eval_count": 5,
        "eval_count": 5
    }

    request = ChatRequest(
        messages=[ChatMessage(role=MessageRole.USER, content="Hello")],
        response_format={"type": "json_object"}
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = await provider.chat(request)
        assert response.message.content == "Hi there"
        assert response.usage["total_tokens"] == 10

        # Verify format=json is in payload
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["format"] == "json"

@pytest.mark.asyncio
async def test_ollama_chat_timeout(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(LoomError) as excinfo:
            await provider.chat(request)
        assert excinfo.value.status_code == 504

@pytest.mark.asyncio
async def test_ollama_chat_stream_success(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    mock_response = MagicMock()
    mock_response.status_code = 200

    chunks = [
        '{"message": {"content": "Hel"}, "done": false}',
        '{"message": {"content": "lo"}, "done": false}',
        '{"done": true, "done_reason": "stop"}'
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
async def test_ollama_chat_stream_error(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    with patch("httpx.AsyncClient.stream", side_effect=Exception("Stream failed")):
        with pytest.raises(LoomError):
            async for _ in provider.chat_stream(request):
                pass

@pytest.mark.asyncio
async def test_ollama_chat_structured_success(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"content": "{\"answer\": \"Paris\"}"},
        "done": True
    }

    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Capital of France?")])
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await provider.chat_structured(request, SampleModel)
        assert result.answer == "Paris"

@pytest.mark.asyncio
async def test_ollama_chat_structured_failure(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {"content": "invalid json"},
        "done": True
    }

    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(LoomError) as excinfo:
            await provider.chat_structured(request, SampleModel)
        assert excinfo.value.status_code == 502

@pytest.mark.asyncio
async def test_ollama_embeddings_success(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"embeddings": [[0.1, 0.2]]}

    request = EmbeddingsRequest(input="test")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        response = await provider.generate_embeddings(request)
        assert response.embeddings == [[0.1, 0.2]]

@pytest.mark.asyncio
async def test_ollama_embeddings_error(provider):
    request = EmbeddingsRequest(input="test")
    with patch("httpx.AsyncClient.post", side_effect=Exception("Embed error")):
        with pytest.raises(LoomError):
            await provider.generate_embeddings(request)

class AsyncMockIterator:
    def __init__(self, items):
        self.items = items
    def __aiter__(self):
        return self
    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)
