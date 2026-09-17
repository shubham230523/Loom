import time
import hashlib
import json
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
from backend.app.database import SessionLocal, ModelRun
from backend.app.services.redis import redis_service
from backend.app.config import settings
from backend.app.utils.logging import logger
from backend.app.api.errors import LoomError

T = TypeVar("T", bound=BaseModel)

class AIGateway:
    """
    Central gateway for all AI operations in Loom.
    Handles provider selection, response normalization, and error aggregation.
    Includes Redis-based caching to minimize costs and latency.
    """
    def __init__(self, provider: Optional[AIProvider] = None):
        self._provider = provider or get_ai_provider()

    def _generate_cache_key(self, request: ChatRequest, operation: str) -> str:
        """Generates a stable hash for a chat request."""
        # Normalize request for hashing
        payload = {
            "model": request.model or settings.DEFAULT_MODEL,
            "messages": [m.model_dump() for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "response_format": request.response_format,
            "operation": operation
        }
        dump = json.dumps(payload, sort_keys=True)
        request_hash = hashlib.sha256(dump.encode()).hexdigest()
        provider_name = type(self._provider).__name__
        return f"ai_cache:{provider_name}:{request_hash}"

    async def chat(self, request: ChatRequest, task: Optional[TaskType] = None) -> ChatResponse:
        """
        Executes a chat completion through the configured provider.
        If task is provided, uses the router to select the model.
        """
        if task:
            request.model = model_router.get_model_for_task(task)

        cache_key = self._generate_cache_key(request, "chat")
        if settings.ENABLE_AI_CACHE:
            cached = await redis_service.get(cache_key)
            if cached:
                logger.info(f"AI Gateway: Cache hit for model {request.model}")
                return ChatResponse.model_validate_json(cached)

        logger.info(f"AI Gateway: Processing chat request with model {request.model}")
        start_time = time.time()
        try:
            response = await self._provider.chat(request)
            duration = time.time() - start_time

            if settings.ENABLE_AI_CACHE:
                await redis_service.set(
                    cache_key,
                    response.model_dump_json(),
                    expire=settings.AI_CACHE_TTL
                )

            await self._record_run(
                model=request.model or "unknown",
                task=task,
                duration=duration,
                usage=response.usage,
                status="success"
            )
            return response
        except Exception as e:
            duration = time.time() - start_time
            await self._record_run(
                model=request.model or "unknown",
                task=task,
                duration=duration,
                status="failed",
                error=str(e)
            )
            self._handle_error(e, "chat")

    async def chat_stream(self, request: ChatRequest, task: Optional[TaskType] = None) -> AsyncIterator[ChatStreamChunk]:
        """
        Executes a streaming chat completion.
        """
        if task:
            request.model = model_router.get_model_for_task(task)

        logger.info(f"AI Gateway: Processing streaming chat request with model {request.model}")
        start_time = time.time()
        try:
            async for chunk in self._provider.chat_stream(request):
                yield chunk

            duration = time.time() - start_time
            await self._record_run(
                model=request.model or "unknown",
                task=task,
                duration=duration,
                status="success"
            )
        except Exception as e:
            duration = time.time() - start_time
            await self._record_run(
                model=request.model or "unknown",
                task=task,
                duration=duration,
                status="failed",
                error=str(e)
            )
            self._handle_error(e, "chat_stream")

    async def chat_structured(
        self,
        request: ChatRequest,
        response_model: Type[T],
        task: Optional[TaskType] = None,
        on_token: Optional[Any] = None
    ) -> T:
        """
        Executes a structured output request, returning a validated Pydantic model.
        """
        if task:
            request.model = model_router.get_model_for_task(task)

        # Cache is disabled when streaming tokens or for debugging tasks to ensure fresh analysis
        use_cache = settings.ENABLE_AI_CACHE and not on_token and task != TaskType.DEBUGGING

        cache_key = self._generate_cache_key(request, f"structured:{response_model.__name__}")
        if use_cache:
            cached = await redis_service.get(cache_key)
            if cached:
                logger.info(f"AI Gateway: Cache hit for structured request {response_model.__name__}")
                return response_model.model_validate_json(cached)

        logger.info(f"AI Gateway: Processing structured request for {response_model.__name__} using model {request.model}")
        start_time = time.time()
        try:
            result = await self._provider.chat_structured(request, response_model, on_token=on_token)
            duration = time.time() - start_time

            if settings.ENABLE_AI_CACHE and not on_token:
                await redis_service.set(
                    cache_key,
                    result.model_dump_json(),
                    expire=settings.AI_CACHE_TTL
                )

            await self._record_run(
                model=request.model or "unknown",
                task=task,
                duration=duration,
                status="success"
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            await self._record_run(
                model=request.model or "unknown",
                task=task,
                duration=duration,
                status="failed",
                error=str(e)
            )
            self._handle_error(e, "chat_structured")

    async def generate_embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        """
        Generates embeddings for the provided input.
        """
        logger.info("AI Gateway: Generating embeddings")
        start_time = time.time()
        try:
            response = await self._provider.generate_embeddings(request)
            duration = time.time() - start_time

            await self._record_run(
                model=request.model or "embeddings",
                duration=duration,
                usage=response.usage,
                status="success"
            )
            return response
        except Exception as e:
            duration = time.time() - start_time
            await self._record_run(
                model=request.model or "embeddings",
                duration=duration,
                status="failed",
                error=str(e)
            )
            self._handle_error(e, "generate_embeddings")

    async def _record_run(
        self,
        model: str,
        duration: float,
        status: str,
        task: Optional[TaskType] = None,
        usage: Optional[Dict[str, int]] = None,
        error: Optional[str] = None
    ):
        """
        Persists model run metrics to the database.
        """
        try:
            async with SessionLocal() as db:
                run = ModelRun(
                    provider=type(self._provider).__name__,
                    model=model,
                    task=task.value if task else None,
                    duration=duration,
                    prompt_tokens=usage.get("prompt_tokens", 0) if usage else 0,
                    completion_tokens=usage.get("completion_tokens", 0) if usage else 0,
                    total_tokens=usage.get("total_tokens", 0) if usage else 0,
                    status=status,
                    error_info=error[:1000] if error else None
                )
                db.add(run)
                await db.commit()
        except Exception as record_error:
            logger.warning(f"Failed to record model run: {str(record_error)}")

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
