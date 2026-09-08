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

class OpenRouterProvider(AIProvider):
    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.timeout = 60.0

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": settings.APP_URL,
            "X-Title": settings.APP_NAME
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _handle_error(self, response: httpx.Response):
        status_code = response.status_code
        try:
            error_data = response.json()
            # OpenRouter usually nests errors
            error_info = error_data.get("error", {})
            message = error_info.get("message", "Unknown OpenRouter Error")
        except Exception:
            message = response.text or "Unknown OpenRouter Error"

        logger.error(f"OpenRouter Error {status_code}: {message}")

        if status_code == 401:
            raise AuthenticationError("OpenRouter authentication failed")
        if status_code == 429:
            raise RateLimitError("OpenRouter rate limit exceeded")

        raise LoomError(f"AI Provider Error: {message}", status_code=status_code)

    async def chat(self, request: ChatRequest) -> ChatResponse:
        url = f"{self.base_url}/chat/completions"
        model = request.model or settings.DEFAULT_MODEL

        payload = {
            "model": model,
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False
        }

        if request.response_format:
            payload["response_format"] = request.response_format

        logger.info(f"OpenRouter: Sending request to {model}")
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)

                if response.status_code != 200:
                    logger.error(f"OpenRouter: Request failed with status {response.status_code}")
                    await self._handle_error(response)

                data = response.json()
                choice = data.get("choices", [{}])[0]
                message_data = choice.get("message", {})

                content = message_data.get("content") or ""
                logger.info(f"OpenRouter: Received response from {model}. Content length: {len(content)}")

                return ChatResponse(
                    message=ChatMessage(
                        role=message_data.get("role", MessageRole.ASSISTANT),
                        content=content
                    ),
                    finish_reason=choice.get("finish_reason"),
                    usage=data.get("usage")
                )
            except httpx.TimeoutException:
                logger.error(f"OpenRouter: Request timed out after {self.timeout}s")
                raise LoomError("OpenRouter request timed out", status_code=504)
            except Exception as e:
                if isinstance(e, LoomError): raise e
                logger.error(f"OpenRouter: Unexpected Error: {str(e)}", exc_info=True)
                raise LoomError(f"AI Provider failure: {str(e)}", status_code=500)

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[ChatStreamChunk]:
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": request.model or settings.DEFAULT_MODEL,
            "messages": [m.model_dump(exclude_none=True) for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", url, headers=self._get_headers(), json=payload) as response:
                    if response.status_code != 200:
                        await self._handle_error(response)

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "): continue
                        if line == "data: [DONE]": break

                        try:
                            data = json.loads(line[6:])
                            choice = data.get("choices", [{}])[0]
                            delta = choice.get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                yield ChatStreamChunk(content=content)

                            if choice.get("finish_reason"):
                                yield ChatStreamChunk(content="", finish_reason=choice.get("finish_reason"))
                        except Exception:
                            continue

            except Exception as e:
                logger.error(f"OpenRouter Streaming Error: {str(e)}")
                raise LoomError(f"AI Streaming failure: {str(e)}", status_code=500)

    async def chat_structured(self, request: ChatRequest, response_model: Type[T]) -> T:
        # OpenRouter supports JSON mode for many models
        request.response_format = {"type": "json_object"}

        # Add system prompt instruction for JSON if not present
        json_instruction = "Return response as a valid JSON object matching the requested schema."
        if not any(json_instruction in m.content for m in request.messages):
             request.messages.append(ChatMessage(role=MessageRole.SYSTEM, content=json_instruction))

        response = await self.chat(request)
        content = response.message.content

        if not content:
            logger.error("OpenRouter: Received empty content in structured request")
            raise LoomError("AI Provider returned empty response", status_code=502)

        # Clean content if it contains markdown markers
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return response_model.model_validate_json(content)
        except Exception as e:
            logger.error(f"OpenRouter: Failed to parse structured response: {str(e)}. Raw Content: {content}")
            raise LoomError("AI Provider returned invalid structured data", status_code=502)

    async def generate_embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        url = f"{self.base_url}/embeddings"

        payload = {
            "model": request.model or "openai/text-embedding-3-small",
            "input": request.input,
            "dimensions": 768 # Force 768 to match DB schema
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)

                if response.status_code != 200:
                    await self._handle_error(response)

                data = response.json()
                # OpenRouter returns standard OpenAI embedding format
                embeddings = [item["embedding"] for item in data.get("data", [])]
                return EmbeddingsResponse(
                    embeddings=embeddings,
                    usage=data.get("usage")
                )
            except Exception as e:
                logger.error(f"OpenRouter Embeddings Error: {str(e)}")
                raise LoomError(f"Failed to generate embeddings: {str(e)}", status_code=500)
