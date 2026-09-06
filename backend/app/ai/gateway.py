from typing import AsyncIterator, List, Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from backend.app.ai.base import AIProvider
from backend.app.ai.factory import get_ai_provider
from backend.app.ai.router import model_router, TaskType
from backend.app.ai.schemas import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    EmbeddingsRequest,
    EmbeddingsResponse,
    ChatMessage
)
from backend.app.utils.logging import logger
from backend.app.api.errors import LoomError

T = TypeVar("T", bound=BaseModel)

class AIGateway:
    """
    Central gateway for all AI operations in Loom.
    Handles provider selection, response normalization, and error aggregation.
    """
    def __init__(self, provider: Optional[AIProvider] = None):
        self._provider = provider or get_ai_provider()

    async def chat(self, request: ChatRequest, task: Optional[TaskType] = None) -> ChatResponse:
        """
        Executes a chat completion through the configured provider.
        If task is provided, uses the router to select the model.
        """
        if task:
            request.model = model_router.get_model_for_task(task)

        logger.info(f"AI Gateway: Processing chat request with model {request.model}")
        try:
            response = await self._provider.chat(request)
            return response
        except Exception as e:
            self._handle_error(e, "chat")

    async def chat_stream(self, request: ChatRequest, task: Optional[TaskType] = None) -> AsyncIterator[ChatStreamChunk]:
        """
        Executes a streaming chat completion.
        """
        if task:
            request.model = model_router.get_model_for_task(task)

        logger.info(f"AI Gateway: Processing streaming chat request with model {request.model}")
        try:
            async for chunk in self._provider.chat_stream(request):
                yield chunk
        except Exception as e:
            self._handle_error(e, "chat_stream")

    async def chat_structured(self, request: ChatRequest, response_model: Type[T], task: Optional[TaskType] = None) -> T:
        """
        Executes a structured output request, returning a validated Pydantic model.
        """
        if task:
            request.model = model_router.get_model_for_task(task)

        logger.info(f"AI Gateway: Processing structured request for {response_model.__name__} using model {request.model}")
        try:
            return await self._provider.chat_structured(request, response_model)
        except Exception as e:
            self._handle_error(e, "chat_structured")

    async def generate_embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        """
        Generates embeddings for the provided input.
        """
        logger.info("AI Gateway: Generating embeddings")
        try:
            return await self._provider.generate_embeddings(request)
        except Exception as e:
            self._handle_error(e, "generate_embeddings")

    def _handle_error(self, e: Exception, operation: str):
        """
        Normalizes errors across different providers.
        """
        if isinstance(e, LoomError):
            raise e

        logger.error(f"AI Gateway error during {operation}: {str(e)}", exc_info=True)
        raise LoomError(
            message=f"AI service currently unavailable ({operation})",
            status_code=503,
            code="AI_GATEWAY_ERROR"
        )

# Global gateway instance
ai_gateway = AIGateway()
