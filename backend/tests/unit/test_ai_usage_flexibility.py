import pytest
from backend.app.ai.schemas import ChatResponse, ChatMessage, MessageRole, EmbeddingsResponse

def test_chat_response_with_nested_usage():
    """Verify that ChatResponse accepts complex nested usage metadata."""
    failing_usage = {
        'prompt_tokens': 10,
        'completion_tokens': 20,
        'total_tokens': 30,
        'prompt_tokens_details': {'cached_tokens': 0, 'audio_tokens': 0},
        'cost_details': {'upstream_inference_cost': 0.0001},
        'completion_tokens_details': {'reasoning_tokens': 0, 'audio_tokens': 0}
    }

    resp = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="Test content"),
        usage=failing_usage,
        finish_reason="stop"
    )

    assert resp.usage['prompt_tokens_details']['cached_tokens'] == 0
    assert resp.usage['cost_details']['upstream_inference_cost'] == 0.0001

def test_embeddings_response_with_nested_usage():
    """Verify that EmbeddingsResponse accepts complex nested usage metadata."""
    usage = {
        'total_tokens': 100,
        'token_details': {'text_tokens': 100, 'image_tokens': 0}
    }

    resp = EmbeddingsResponse(
        embeddings=[[0.1, 0.2, 0.3]],
        usage=usage
    )

    assert resp.usage['token_details']['text_tokens'] == 100
