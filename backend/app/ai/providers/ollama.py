import json
import httpx
from typing import AsyncIterator, List, Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from backend.app.ai.base import AIProvider
from backend.app.ai.schemas import (
    ChatRequest,
    ChatResponse,
    ChatStreamChunk,
    EmbeddingsRequest,
    EmbeddingsResponse,
    ChatMessage,
    MessageRole
)
from backend.app.config import settings
from backend.app.api.errors import LoomError, AuthenticationError, RateLimitError
from backend.app.utils.logging import logger

T = TypeVar("T", bound=BaseModel)

class OllamaCloudProvider(AIProvider):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.api_key = settings.OLLAMA_API_KEY
        self.timeout = 60.0 # Long timeout for AI generation

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _handle_error(self, response: httpx.Response):
        status_code = response.status_code
        try:
            error_data = response.json()
            message = error_data.get("error", "Unknown Ollama Cloud Error")
        except Exception:
            message = response.text or "Unknown Ollama Cloud Error"

        logger.error(f"Ollama Cloud Error {status_code}: {message}")

        if status_code == 401:
            raise AuthenticationError("Ollama Cloud authentication failed")
        if status_code == 429:
            raise RateLimitError("Ollama Cloud rate limit exceeded")

        raise LoomError(f"AI Provider Error: {message}", status_code=status_code)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": request.model or settings.DEFAULT_MODEL,
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }

        if request.response_format:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)

                if response.status_code != 200:
                    await self._handle_error(response)

                data = response.json()
                message = data.get("message", {})

                return ChatResponse(
                    message=ChatMessage(
                        role=message.get("role", MessageRole.ASSISTANT),
                        content=message.get("content", "")
                    ),
                    finish_reason=data.get("done_reason"),
                    usage={
                        "prompt_tokens": data.get("prompt_eval_count", 0),
                        "completion_tokens": data.get("eval_count", 0),
                        "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    }
                )
            except httpx.TimeoutException:
                raise LoomError("AI Provider request timed out", status_code=504)
            except Exception as e:
                if isinstance(e, LoomError): raise e
                logger.error(f"Ollama Cloud Unexpected Error: {str(e)}")
                raise LoomError(f"AI Provider failure: {str(e)}", status_code=500)

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[ChatStreamChunk]:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": request.model or settings.DEFAULT_MODEL,
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                    if response.status_code != 200:
                        await self._handle_error(response)

                    async for line in response.aiter_lines():
                        if not line: continue
                        data = json.loads(line)

                        if data.get("done"):
                            yield ChatStreamChunk(content="", finish_reason=data.get("done_reason"))
                        else:
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield ChatStreamChunk(content=content)

            except Exception as e:
                logger.error(f"Ollama Cloud Streaming Error: {str(e)}")
                raise LoomError(f"AI Streaming failure: {str(e)}", status_code=500)

    async def chat_structured(self, request: ChatRequest, response_model: Type[T]) -> T:
        # For Ollama, we use JSON mode and manual validation
        # Most "Cloud" providers supporting Ollama API also support format="json"
        request.response_format = {"type": "json_object"}

        response = await self.chat(request)
        content = response.message.content

        try:
            return response_model.model_validate_json(content)
        except Exception as e:
            logger.error(f"Failed to parse structured AI response: {str(e)}. Content: {content}")
            raise LoomError("AI Provider returned invalid structured data", status_code=502)

    async def generate_embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        url = f"{self.base_url}/api/embed"

        inputs = request.input if isinstance(request.input, list) else [request.input]

        payload = {
            "model": request.model or "nomic-embed-text", # Default embedding model for Ollama
            "input": inputs
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)

                if response.status_code != 200:
                    await self._handle_error(response)

                data = response.json()
                return EmbeddingsResponse(
                    embeddings=data.get("embeddings", []),
                    usage={"total_tokens": 0} # Ollama embed doesn't always return usage
                )
            except Exception as e:
                logger.error(f"Ollama Cloud Embeddings Error: {str(e)}")
                raise LoomError(f"Failed to generate embeddings: {str(e)}", status_code=500)
