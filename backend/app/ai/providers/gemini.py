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

class GeminiProvider(AIProvider):
    def __init__(self):
        self.base_url = settings.GEMINI_BASE_URL
        self.api_key = settings.GEMINI_API_KEY
        self.timeout = 120.0

    def _get_url(self, model: str, action: str) -> str:
        # Action is usually generateContent or streamGenerateContent
        return f"{self.base_url}/models/{model}:{action}?key={self.api_key}"

    async def _handle_error(self, response: httpx.Response):
        status_code = response.status_code
        try:
            # Ensure content is read for both streaming and normal responses
            content = await response.aread()
            error_data = json.loads(content)
            error_info = error_data.get("error", {})
            message = error_info.get("message", "Unknown Gemini Error")
        except Exception:
            try:
                # If we couldn't parse JSON, try to get raw text
                message = response.text if not response.is_closed else "Unknown Gemini Error (response closed)"
            except Exception:
                message = "Unknown Gemini Error"

        logger.error(f"Gemini Error {status_code}: {message}")

        if status_code == 401 or status_code == 403:
            raise AuthenticationError("Gemini authentication failed")
        if status_code == 429:
            raise RateLimitError("Gemini rate limit exceeded")

        raise LoomError(f"AI Provider Error: {message}", status_code=status_code)

    def _map_messages(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        """
        Maps standard ChatMessages to Gemini format.
        Handles system messages and multimodal file data.
        """
        system_instruction = None
        contents = []

        # If any message has file_data, we use the content array structure (multimodal)
        has_file = any(m.file_data for m in messages)

        if has_file:
            for m in messages:
                if m.role == MessageRole.SYSTEM:
                    system_instruction = {"parts": [{"text": m.content}]}
                else:
                    role = "user" if m.role == MessageRole.USER else "model"
                    parts = [{"text": m.content}]
                    if m.file_data:
                        parts.append({
                            "inlineData": {
                                "data": m.file_data["data"],
                                "mimeType": m.file_data.get("mime_type", "application/octet-stream")
                            }
                        })
                    contents.append({
                        "role": role,
                        "parts": parts
                    })
        else:
            # ApplyAI style: combine into a single prompt for standard text flow
            # This often leads to better instruction following for text-only tasks
            prompt_parts = []
            for m in messages:
                if m.role == MessageRole.SYSTEM:
                    system_instruction = {"parts": [{"text": m.content}]}
                else:
                    prompt_parts.append(f"[{m.role.upper()}]: {m.content}")

            prompt = "\n\n".join(prompt_parts)
            if not prompt:
                # Fallback if only system instruction exists
                prompt = "Please proceed."

            contents = [{
                "role": "user",
                "parts": [{"text": prompt}]
            }]

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

        if request.response_format:
            payload["generationConfig"]["response_mime_type"] = "application/json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        await self._handle_error(response)

                    # Better streaming parser for Gemini's JSON array format
                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk
                        # Gemini streams objects inside a JSON array
                        # We need to extract each object
                        while True:
                            buffer = buffer.strip()
                            if not buffer:
                                break

                            # Handle array start/end/comma
                            if buffer.startswith("["):
                                buffer = buffer[1:]
                                continue
                            if buffer.startswith(","):
                                buffer = buffer[1:]
                                continue
                            if buffer.startswith("]"):
                                buffer = buffer[1:]
                                break

                            # Try to find a complete JSON object in the buffer
                            try:
                                # Count braces to find object end
                                if not buffer.startswith("{"):
                                    # Skip anything that's not a start of an object
                                    # (might be whitespace or array markers we missed)
                                    first_brace = buffer.find("{")
                                    if first_brace == -1:
                                        break
                                    buffer = buffer[first_brace:]

                                brace_count = 0
                                found_end = False
                                in_string = False
                                escaped = False

                                for i, char in enumerate(buffer):
                                    if char == '"' and not escaped:
                                        in_string = not in_string
                                    if not in_string:
                                        if char == "{":
                                            brace_count += 1
                                        elif char == "}":
                                            brace_count -= 1
                                            if brace_count == 0:
                                                obj_str = buffer[:i+1]
                                                buffer = buffer[i+1:]
                                                found_end = True
                                                break

                                    if char == "\\" and not escaped:
                                        escaped = True
                                    else:
                                        escaped = False

                                if found_end:
                                    data = json.loads(obj_str)
                                    candidate = data.get("candidates", [{}])[0]
                                    content = candidate.get("content", {})
                                    parts = content.get("parts", [{}])
                                    text = parts[0].get("text", "")

                                    if text:
                                        yield ChatStreamChunk(content=text)

                                    if candidate.get("finishReason"):
                                        yield ChatStreamChunk(content="", finish_reason=candidate.get("finishReason"))
                                else:
                                    # Incomplete object, wait for more data
                                    break
                            except Exception:
                                # If parsing fails, it might be an incomplete object
                                break

            except Exception as e:
                logger.error(f"Gemini Streaming Error: {str(e)}")
                raise LoomError(f"AI Streaming failure: {str(e)}", status_code=500)

    async def chat_structured(
        self,
        request: ChatRequest,
        response_model: Type[T],
        on_token: Optional[Any] = None
    ) -> T:
        # Gemini supports response_mime_type="application/json"
        request.response_format = {"type": "json_object"}

        # ApplyAI Style: Inject schema directly into the prompt for maximum accuracy
        schema_json = json.dumps(response_model.model_json_schema(), indent=2)
        json_instruction = (
            f"\n\nCRITICAL: Your response MUST be a valid JSON object matching this schema:\n{schema_json}\n"
            f"Return ONLY the JSON object. Do not include markdown formatting or explanations."
        )

        # Append instruction to the last user message
        if request.messages:
            last_msg = request.messages[-1]
            if last_msg.role == MessageRole.USER:
                last_msg.content += json_instruction
            else:
                request.messages.append(ChatMessage(role=MessageRole.USER, content=json_instruction))
        else:
             request.messages.append(ChatMessage(role=MessageRole.USER, content=json_instruction))

        content = ""
        last_finish_reason = None
        if on_token:
            try:
                async for chunk in self.chat_stream(request):
                    if chunk.content:
                        content += chunk.content
                        await on_token(chunk.content)
                    if chunk.finish_reason:
                        last_finish_reason = chunk.finish_reason
            except Exception as stream_err:
                logger.error(f"Gemini Streaming error during structured parse: {str(stream_err)}")
                # DO NOT proceed if the stream was interrupted, as the JSON will be malformed
                raise stream_err
        else:
            response = await self.chat(request)
            content = response.message.content
            last_finish_reason = response.finish_reason

        if not content:
            logger.error("Gemini: Received empty content in structured request")
            raise LoomError("AI Provider returned empty response", status_code=502)

        # ApplyAI Style: Clean content using regex to find JSON block
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', content)
        if json_match:
            content = json_match.group(0)

        # Cleanup any potential markdown or whitespace
        content = content.strip()

        try:
            return response_model.model_validate_json(content)
        except Exception as first_error:
            logger.warning(f"Gemini: First validation attempt failed: {str(first_error)}. Attempting robust parse...")
            try:
                # Try to parse as raw dict first
                try:
                    data = json.loads(content)
                except Exception:
                    clean_content = re.sub(r',\s*([\]}])', r'\1', content)
                    data = json.loads(clean_content)

                # Use the same robust mapping logic as OpenRouter
                if isinstance(data, dict):
                    for model_field in response_model.model_fields:
                        if model_field not in data:
                            # Try variations
                            normalized_model = model_field.replace("_", "").lower()
                            for k, v in data.items():
                                if k.lower().replace("_", "").replace(" ", "").replace("analysis", "") == normalized_model:
                                    data[model_field] = v
                                    break

                            if model_field not in data:
                                # camelCase
                                camel_field = "".join(word.capitalize() if i > 0 else word for i, word in enumerate(model_field.split("_")))
                                if camel_field in data: data[model_field] = data[camel_field]

                    # Specific mapping for common fields
                    if "new_content" not in data:
                        for k in ["updated_content", "updatedContent", "content", "code", "text"]:
                            if k in data: data["new_content"] = data[k]; break

                    if "root_cause_analysis" not in data:
                        for k in ["root_cause", "rootCause", "explanation", "analysis"]:
                            if k in data: data["root_cause_analysis"] = data[k]; break

                    if "suggested_fix" not in data:
                        for k in ["fix", "suggestedFix", "solution"]:
                            if k in data: data["suggested_fix"] = data[k]; break

                    # Specific mapping for CodeReviewResult
                    if "summary" not in data:
                        for k in ["feedback", "overview", "review_summary"]:
                            if k in data: data["summary"] = data[k]; break

                    if "confidence" not in data:
                        for k in ["score", "certainty"]:
                            if k in data: data["confidence"] = data[k]; break
                        if "confidence" not in data: data["confidence"] = 0.9

                    if "issues" not in data:
                        for k in ["findings", "suggested_fixes", "problems"]:
                            if k in data:
                                # Handle cases where model returns strings instead of objects for fixes
                                if isinstance(data[k], list) and data[k] and isinstance(data[k][0], str):
                                    data["issues"] = [{"description": f} for f in data[k]]
                                else:
                                    data["issues"] = data[k]
                                break
                        if "issues" not in data: data["issues"] = []

                    # Catch-all for any other missing required fields
                    for field_name, field_info in response_model.model_fields.items():
                        if field_name not in data and field_info.is_required():
                            # If it's a string, provide empty
                            if field_info.annotation is str: data[field_name] = ""
                            # If it's a list, provide empty
                            elif getattr(field_info.annotation, "__origin__", None) is list: data[field_name] = []
                            # If it's a float/int
                            elif field_info.annotation in [float, int]: data[field_name] = 0

                logger.debug(f"Gemini: Validating data with keys: {list(data.keys())}")
                return response_model.model_validate(data)
            except Exception as final_error:
                logger.error(f"Failed to parse structured Gemini response: {str(final_error)}. Content: {content}")
                raise LoomError("AI Provider returned invalid structured data", status_code=502)

    async def generate_embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        model = request.model or "text-embedding-004"
        # Use v1 for stable embedding models
        v1_base = "https://generativelanguage.googleapis.com/v1"

        # Ensure model name is properly formatted
        model_id = model if model.startswith("models/") else f"models/{model}"
        url = f"{v1_base}/{model_id}:embedContent?key={self.api_key}"

        inputs = request.input if isinstance(request.input, list) else [request.input]

        embeddings = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for text in inputs:
                # The REST API for embedContent doesn't need 'model' in payload when in URL
                payload = {
                    "content": {"parts": [{"text": text}]}
                }
                try:
                    response = await client.post(url, json=payload)
                    if response.status_code != 200:
                        await self._handle_error(response)

                    data = response.json()
                    embeddings.append(data.get("embedding", {}).get("values", []))
                except Exception as e:
                    if isinstance(e, LoomError): raise e
                    logger.error(f"Gemini Embeddings Error: {str(e)}")
                    raise LoomError(f"Failed to generate embeddings: {str(e)}", status_code=500)

        return EmbeddingsResponse(embeddings=embeddings)
