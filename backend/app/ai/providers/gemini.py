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

class GeminiProvider(AIProvider):
    def __init__(self):
        self.base_url = settings.GEMINI_BASE_URL
        self.api_key = settings.GEMINI_API_KEY
        self.timeout = 60.0

    def _get_url(self, model: str, action: str) -> str:
        # Action is usually generateContent or streamGenerateContent
        return f"{self.base_url}/models/{model}:{action}?key={self.api_key}"

    async def _handle_error(self, response: httpx.Response):
        status_code = response.status_code
        try:
            error_data = response.json()
            error_info = error_data.get("error", {})
            message = error_info.get("message", "Unknown Gemini Error")
        except Exception:
            message = response.text or "Unknown Gemini Error"

        logger.error(f"Gemini Error {status_code}: {message}")

        if status_code == 401 or status_code == 403:
            raise AuthenticationError("Gemini authentication failed")
        if status_code == 429:
            raise RateLimitError("Gemini rate limit exceeded")

        raise LoomError(f"AI Provider Error: {message}", status_code=status_code)

    def _map_messages(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """
        Maps standard ChatMessages to Gemini format.
        Handles system messages separately.
        """
        system_instruction = None
        contents = []

        for m in messages:
            if m.role == MessageRole.SYSTEM:
                system_instruction = {"parts": [{"text": m.content}]}
            else:
                role = "user" if m.role == MessageRole.USER else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": m.content}]
                })

        return {
            "contents": contents,
            "system_instruction": system_instruction
        }

    async def chat(self, request: ChatRequest) -> ChatResponse:
        model = request.model or settings.DEFAULT_MODEL
        # Remove version prefix if present for direct API use (e.g. models/gemini-1.5-pro -> gemini-1.5-pro)
        model_name = model.split("/")[-1]
        url = self._get_url(model_name, "generateContent")

        mapped = self._map_messages(request.messages)
        payload = {
            "contents": mapped["contents"],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            }
        }
        if mapped["system_instruction"]:
            payload["system_instruction"] = mapped["system_instruction"]

        if request.response_format:
             payload["generationConfig"]["response_mime_type"] = "application/json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)

                if response.status_code != 200:
                    await self._handle_error(response)

                data = response.json()
                candidate = data.get("candidates", [{}])[0]
                content = candidate.get("content", {})
                parts = content.get("parts", [{}])
                text = parts[0].get("text", "")

                return ChatResponse(
                    message=ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content=text
                    ),
                    finish_reason=candidate.get("finishReason"),
                    usage=data.get("usageMetadata")
                )
            except httpx.TimeoutException:
                raise LoomError("Gemini request timed out", status_code=504)
            except Exception as e:
                if isinstance(e, LoomError): raise e
                logger.error(f"Gemini Unexpected Error: {str(e)}")
                raise LoomError(f"AI Provider failure: {str(e)}", status_code=500)

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[ChatStreamChunk]:
        model = request.model or settings.DEFAULT_MODEL
        model_name = model.split("/")[-1]
        url = self._get_url(model_name, "streamGenerateContent")

        mapped = self._map_messages(request.messages)
        payload = {
            "contents": mapped["contents"],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            }
        }
        if mapped["system_instruction"]:
            payload["system_instruction"] = mapped["system_instruction"]

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        await self._handle_error(response)

                    # Gemini streaming returns a JSON array of responses
                    # but it is usually sent chunk by chunk
                    async for line in response.aiter_lines():
                        if not line: continue
                        # Strip comma if it's part of the array
                        clean_line = line.strip().strip("[").strip("]").strip(",")
                        if not clean_line: continue

                        try:
                            data = json.loads(clean_line)
                            candidate = data.get("candidates", [{}])[0]
                            content = candidate.get("content", {})
                            parts = content.get("parts", [{}])
                            text = parts[0].get("text", "")

                            if text:
                                yield ChatStreamChunk(content=text)

                            if candidate.get("finishReason"):
                                yield ChatStreamChunk(content="", finish_reason=candidate.get("finishReason"))
                        except Exception:
                            continue

            except Exception as e:
                logger.error(f"Gemini Streaming Error: {str(e)}")
                raise LoomError(f"AI Streaming failure: {str(e)}", status_code=500)

    async def chat_structured(self, request: ChatRequest, response_model: Type[T]) -> T:
        # Gemini supports response_mime_type="application/json"
        request.response_format = {"type": "json_object"}

        # Add instruction to ensure JSON
        json_instruction = f"Return response as a valid JSON object matching the following schema: {response_model.model_json_schema()}"
        request.messages.append(ChatMessage(role=MessageRole.SYSTEM, content=json_instruction))

        response = await self.chat(request)
        content = response.message.content

        try:
            return response_model.model_validate_json(content)
        except Exception as e:
            logger.error(f"Failed to parse structured Gemini response: {str(e)}. Content: {content}")
            raise LoomError("AI Provider returned invalid structured data", status_code=502)

    async def generate_embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        model = request.model or "text-embedding-004"
        url = self._get_url(model, "embedContent")

        inputs = request.input if isinstance(request.input, list) else [request.input]

        # Gemini embedContent takes a single content or batchEmbedContents
        # For simplicity, we implement single or loop
        embeddings = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for text in inputs:
                payload = {
                    "model": f"models/{model}",
                    "content": {"parts": [{"text": text}]}
                }
                try:
                    response = await client.post(url, json=payload)
                    if response.status_code != 200:
                        await self._handle_error(response)

                    data = response.json()
                    embeddings.append(data.get("embedding", {}).get("values", []))
                except Exception as e:
                    logger.error(f"Gemini Embeddings Error: {str(e)}")
                    raise LoomError(f"Failed to generate embeddings: {str(e)}", status_code=500)

        return EmbeddingsResponse(embeddings=embeddings)
