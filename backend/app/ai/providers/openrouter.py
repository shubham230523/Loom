import json
import httpx
import re
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
        self.timeout = 120.0

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
            # Check if this is a streaming response that hasn't been read
            try:
                # Regular response has .content available, streaming doesn't
                _ = response.content
            except httpx.ResponseNotRead:
                await response.aread()

            error_data = response.json()
            # OpenRouter usually nests errors
            error_info = error_data.get("error", {})
            message = error_info.get("message", "Unknown OpenRouter Error")
        except Exception:
            try:
                message = response.text or "Unknown OpenRouter Error"
            except Exception:
                message = "Unknown OpenRouter Error (could not read response)"

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

    def _repair_json(self, json_str: str) -> str:
        """Attempts to repair truncated or malformed JSON by balancing braces/quotes."""
        json_str = json_str.strip()
        if not json_str:
            return json_str

        # If it seems to end in the middle of a string
        if json_str.count('"') % 2 != 0:
            # If the last character is a backslash, remove it to avoid escaping our closing quote
            if json_str.endswith('\\'):
                json_str = json_str[:-1]
            json_str += '"'

        # Balance braces
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)

        # Balance brackets
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)

        return json_str

    async def chat_structured(
        self,
        request: ChatRequest,
        response_model: Type[T],
        on_token: Optional[Any] = None
    ) -> T:
        # OpenRouter supports JSON mode for many models
        request.response_format = {"type": "json_object"}

        # Add system prompt instruction for JSON if not present
        json_instruction = "Return response as a valid JSON object matching the requested schema."
        if not any(json_instruction in m.content for m in request.messages):
             request.messages.append(ChatMessage(role=MessageRole.SYSTEM, content=json_instruction))

        # Retry loop for structured output parsing
        max_parse_retries = 2
        last_error = None

        for attempt in range(max_parse_retries + 1):
            content = ""
            last_finish_reason = None
            if on_token:
                # Stream the structured response if a callback is provided
                async for chunk in self.chat_stream(request):
                    if chunk.content:
                        content += chunk.content
                        await on_token(chunk.content)
                    if chunk.finish_reason:
                        last_finish_reason = chunk.finish_reason
            else:
                # Fallback to standard non-streaming chat
                response = await self.chat(request)
                content = response.message.content
                last_finish_reason = response.finish_reason

            if last_finish_reason == "length":
                logger.warning(f"OpenRouter: Response truncated due to length for model {request.model}")

            if not content:
                if attempt < max_parse_retries: continue
                logger.error("OpenRouter: Received empty content in structured request")
                raise LoomError("AI Provider returned empty response", status_code=502)

            # Clean content if it contains markdown markers
            content_original = content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                # Be careful with raw ``` - it might be bash or something else
                parts = content.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("{") and part.endswith("}"):
                        content = part
                        break
                    # Try to find a part that looks like JSON even if it has a language tag like ```bash
                    if "\n{" in part or part.startswith("{\n"):
                        potential_json = part[part.find("{"):part.rfind("}")+1]
                        if potential_json:
                            content = potential_json
                            break

            # If still doesn't look like JSON, try a regex-like extraction of the first { and last }
            if not (content.strip().startswith("{") and content.strip().endswith("}")):
                start = content_original.find("{")
                end = content_original.rfind("}")
                if start != -1 and end != -1 and end > start:
                    content = content_original[start:end+1]

            try:
                # Attempt 1: Native Pydantic validation from JSON string
                return response_model.model_validate_json(content)
            except Exception as first_error:
                last_error = first_error
                logger.warning(f"OpenRouter: Structured parse attempt {attempt + 1} failed: {str(first_error)}")

                try:
                    # Attempt 2: Manual JSON load + Cleaning + Model Validate
                    try:
                        data = json.loads(content)
                    except Exception:
                        # If content is still messy, try to clean it even more (e.g. trailing commas)
                        clean_content = re.sub(r',\s*([\]}])', r'\1', content)
                        try:
                            data = json.loads(clean_content)
                        except Exception:
                            # Last ditch: try to repair truncated JSON
                            repaired = self._repair_json(content)
                            data = json.loads(repaired)

                    # Mapping logic (unchanged from your robust version but wrapped in the loop)
                    if isinstance(data, dict):
                        # ... mapping logic ...
                        for model_field in response_model.model_fields:
                            if model_field not in data:
                                normalized_model = model_field.replace("_", "").lower()
                                for k, v in data.items():
                                    if k.lower().replace("_", "").replace(" ", "").replace("analysis", "") == normalized_model:
                                        data[model_field] = v
                                        break
                                # ... existing camelCase/Spaced mapping ...
                                if model_field not in data:
                                    camel_field = "".join(word.capitalize() if i > 0 else word for i, word in enumerate(model_field.split("_")))
                                    if camel_field in data: data[model_field] = data[camel_field]
                                if model_field not in data:
                                    spaced_field = model_field.replace("_", " ")
                                    if spaced_field in data: data[model_field] = data[spaced_field]

                        # Specific type handling
                        if "new_content" not in data:
                            for k in ["updated_content", "updatedContent", "content", "code", "text"]:
                                if k in data: data["new_content"] = data[k]; break

                        if "root_cause_analysis" not in data:
                            for k in ["root_cause", "rootCause", "explanation", "analysis"]:
                                if k in data: data["root_cause_analysis"] = data[k]; break

                        if "suggested_fix" not in data:
                            for k in ["fix", "suggestedFix", "solution"]:
                                if k in data: data["suggested_fix"] = data[k]; break

                        if "affected_files" not in data:
                            data["affected_files"] = data.get("files", data.get("path", []))
                            if isinstance(data["affected_files"], str): data["affected_files"] = [data["affected_files"]]

                    return response_model.model_validate(data)
                except Exception as final_error:
                    last_error = final_error
                    if attempt < max_parse_retries:
                        logger.info(f"OpenRouter: Retrying structured request (Attempt {attempt + 2})")
                        # Add a hint to the next attempt if possible or just retry
                        continue

        logger.error(f"OpenRouter: All structured parse attempts failed. Last error: {str(last_error)}. Content: {content}")
        raise LoomError(f"AI Provider returned invalid structured data after retries: {str(last_error)}", status_code=502)

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
