from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal
from enum import Enum

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    response_format: Optional[Dict[str, Any]] = None # For JSON mode or structured outputs

class ChatResponse(BaseModel):
    message: ChatMessage
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None

class ChatStreamChunk(BaseModel):
    content: str
    finish_reason: Optional[str] = None

class EmbeddingsRequest(BaseModel):
    input: Union[str, List[str]]
    model: Optional[str] = None

class EmbeddingsResponse(BaseModel):
    embeddings: List[List[float]]
    usage: Optional[Dict[str, int]] = None
