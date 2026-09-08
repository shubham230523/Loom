from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    message: ChatMessage
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None

# This is what OpenRouter/Gemini might be returning
failing_usage = {
    'prompt_tokens': 10,
    'completion_tokens': 20,
    'total_tokens': 30,
    'prompt_tokens_details': {'cached_tokens': 0},
    'cost_details': {'upstream_inference_cost': 0},
    'completion_tokens_details': {'reasoning_tokens': 0}
}

try:
    resp = ChatResponse(
        message=ChatMessage(role="assistant", content="hello"),
        usage=failing_usage,
        finish_reason="stop"
    )
    print("Success!")
    print(resp.model_dump())
except Exception as e:
    print(f"Failed with error: {e}")
