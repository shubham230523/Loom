import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

try:
    from app.ai.schemas import ChatResponse, ChatMessage, MessageRole
    print("Import successful")

    failing_usage = {
        'prompt_tokens': 10,
        'completion_tokens': 20,
        'total_tokens': 30,
        'prompt_tokens_details': {'cached_tokens': 0},
        'cost_details': {'upstream_inference_cost': 0},
        'completion_tokens_details': {'reasoning_tokens': 0}
    }

    resp = ChatResponse(
        message=ChatMessage(role=MessageRole.ASSISTANT, content="hello"),
        usage=failing_usage,
        finish_reason="stop"
    )
    print("Success!")
    print(resp.model_dump())
except Exception as e:
    print(f"Failed with error: {e}")
