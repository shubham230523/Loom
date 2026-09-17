import pytest
import httpx
import json
from unittest.mock import AsyncMock, MagicMock, patch
from backend.app.ai.providers.openrouter import OpenRouterProvider
from backend.app.ai.schemas import ChatRequest, ChatMessage, MessageRole, EmbeddingsRequest
from backend.app.api.errors import LoomError, AuthenticationError, RateLimitError
from pydantic import BaseModel, RootModel
from typing import List

class MockModel(BaseModel):
    my_field: str
    my_list: List[str]

class SolutionPlanOutput(BaseModel):
    problem: str
    implementation_steps: List[str]
    relevant_files: List[str]

class RootListModel(RootModel):
    root: List[str]

@pytest.fixture
def provider():
    return OpenRouterProvider()

def test_openrouter_get_headers(provider):
    headers = provider._get_headers()
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer")
    # settings.APP_NAME seems to be "Loom API" in this environment
    assert headers["X-Title"] in ["Loom", "Loom API"]

def test_openrouter_get_headers_no_key(provider):
    provider.api_key = None
    headers = provider._get_headers()
    assert "Authorization" not in headers

@pytest.mark.asyncio
async def test_openrouter_handle_error_variants(provider):
    mock_response = MagicMock()

    # 401
    mock_response.status_code = 401
    mock_response.json.return_value = {"error": {"message": "Unauthorized"}}
    with pytest.raises(AuthenticationError):
        await provider._handle_error(mock_response)

    # 429
    mock_response.status_code = 429
    with pytest.raises(RateLimitError):
        await provider._handle_error(mock_response)

    # Generic error with no JSON
    mock_response.status_code = 500
    mock_response.json.side_effect = Exception("Not JSON")
    mock_response.text = "Error Text"
    with pytest.raises(LoomError) as excinfo:
        await provider._handle_error(mock_response)
    assert "Error Text" in str(excinfo.value)

@pytest.mark.asyncio
async def test_openrouter_chat_success(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{
            "message": {"role": "assistant", "content": "OpenRouter response"},
            "finish_reason": "stop"
        }],
        "usage": {"total_tokens": 50}
    }

    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hello")])

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        response = await provider.chat(request)
        assert response.message.content == "OpenRouter response"
        assert response.usage["total_tokens"] == 50

@pytest.mark.asyncio
async def test_openrouter_chat_timeout(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        with pytest.raises(LoomError) as excinfo:
            await provider.chat(request)
        assert excinfo.value.status_code == 504

@pytest.mark.asyncio
async def test_openrouter_chat_stream_success(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    mock_response = MagicMock()
    mock_response.status_code = 200

    chunks = [
        'data: {"choices": [{"delta": {"content": "Hel"}}]}',
        'data: {"choices": [{"delta": {"content": "lo"}, "finish_reason": "stop"}]}',
        'data: [DONE]'
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
async def test_openrouter_chat_stream_error(provider):
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Hi")])
    with patch("httpx.AsyncClient.stream", side_effect=Exception("Stream failed")):
        with pytest.raises(LoomError):
            async for _ in provider.chat_stream(request):
                pass

@pytest.mark.asyncio
async def test_openrouter_chat_structured_robust_parse(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Test: Markdown + Wrapper field + camelCase + Single item for list
    mock_response.json.return_value = {
        "choices": [{
            "message": {"role": "assistant", "content": "```json\n{\"wrapper\": {\"myField\": \"val\", \"my_list\": \"single_item\"}}\n```"},
        }]
    }

    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Req")])

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await provider.chat_structured(request, MockModel)
        assert result.my_field == "val"
        assert result.my_list == ["single_item"]

@pytest.mark.asyncio
async def test_openrouter_chat_structured_mapping(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Test specific mappings like title -> problem, implementationPlan -> implementation_steps
    mock_response.json.return_value = {
        "choices": [{
            "message": {"role": "assistant", "content": "{\"title\": \"Prob\", \"implementationPlan\": [\"step1\"], \"affectedFiles\": [\"file1\"]}"},
        }]
    }

    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Req")])

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response

        result = await provider.chat_structured(request, SolutionPlanOutput)
        assert result.problem == "Prob"
        assert result.implementation_steps == ["step1"]
        assert result.relevant_files == ["file1"]

@pytest.mark.asyncio
async def test_openrouter_chat_structured_root_list(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Test RootModel with a dict containing a list
    mock_response.json.return_value = {
        "choices": [{
            "message": {"role": "assistant", "content": "{\"items\": [\"item1\", \"item2\"]}"},
        }]
    }
    request = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="Req")])

    # Monkeypatch to trigger the legacy __root__ check in openrouter.py
    setattr(RootListModel, "__root__", True)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await provider.chat_structured(request, RootListModel)
        assert result.root == ["item1", "item2"]

    delattr(RootListModel, "__root__")

@pytest.mark.asyncio
async def test_openrouter_chat_structured_empty(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"message": {"content": ""}}]}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        with pytest.raises(LoomError) as excinfo:
            await provider.chat_structured(request=ChatRequest(messages=[]), response_model=MockModel)
        assert excinfo.value.status_code == 502

@pytest.mark.asyncio
async def test_openrouter_embeddings_success(provider):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [{"embedding": [0.1, 0.2]}],
        "usage": {"total_tokens": 5}
    }

    request = EmbeddingsRequest(input="test")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        response = await provider.generate_embeddings(request)
        assert response.embeddings == [[0.1, 0.2]]
        assert response.usage["total_tokens"] == 5

@pytest.mark.asyncio
async def test_openrouter_embeddings_error(provider):
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
