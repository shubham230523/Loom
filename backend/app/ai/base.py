from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional, Type, TypeVar
from pydantic import BaseModel
from backend.app.ai.schemas import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    EmbeddingsRequest,
    EmbeddingsResponse
)

T = TypeVar("T", bound=BaseModel)

class AIProvider(ABC):
    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        Sends a chat request and returns a complete response.
        """
        pass

    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[ChatStreamChunk]:
        """
        Sends a chat request and returns an async iterator of chunks.
        """
        pass

    @abstractmethod
    async def chat_structured(self, request: ChatRequest, response_model: Type[T]) -> T:
        """
        Sends a chat request and returns a validated Pydantic model.
        """
        pass

    @abstractmethod
    async def generate_embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        """
        Generates embeddings for the provided input.
        """
        pass
