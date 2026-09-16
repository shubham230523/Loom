import json
import asyncio
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
from backend.app.utils.logging import logger

T = TypeVar("T", bound=BaseModel)

class MockAIProvider(AIProvider):
    """
    A mock provider for testing UI and workflows without real AI calls.
    Returns realistic but static data matching requested schemas.
    """
    async def chat(self, request: ChatRequest) -> ChatResponse:
        logger.info("MockAIProvider: Simulating chat response")
        await asyncio.sleep(0.5) # Simulate latency

        return ChatResponse(
            message=ChatMessage(
                role=MessageRole.ASSISTANT,
                content="This is a mock AI response. The system is working correctly in mock mode."
            ),
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[ChatStreamChunk]:
        logger.info("MockAIProvider: Simulating streaming response")
        words = "This is a streaming mock response from Loom.".split()
        for word in words:
            await asyncio.sleep(0.1)
            yield ChatStreamChunk(content=word + " ")
        yield ChatStreamChunk(content="", finish_reason="stop")

    async def chat_structured(self, request: ChatRequest, response_model: Type[T]) -> T:
        logger.info(f"MockAIProvider: Simulating structured response for {response_model.__name__}")
        await asyncio.sleep(1.0)

        # Basic mock data generator based on common models in Loom
        model_name = response_model.__name__
        data = {}

        if model_name == "OpportunityList":
            data = {
                "opportunities": [
                    {
                        "title": "Fix TODO in auth.py",
                        "description": "The auth service has a TODO regarding token expiration handling. This should be implemented to improve security.",
                        "type": "bug",
                        "impact": "High",
                        "difficulty": "Easy",
                        "confidence": 0.95,
                        "evidence_source": "auth.py:42",
                        "affected_files": ["backend/app/security/auth.py"]
                    },
                    {
                        "title": "Optimize Database Queries in Discover",
                        "description": "Some queries in the discovery service are missing indexes or using inefficient joins.",
                        "type": "refactor",
                        "impact": "Medium",
                        "difficulty": "Intermediate",
                        "confidence": 0.85,
                        "evidence_source": "opportunity_service.py",
                        "affected_files": ["backend/app/repository/opportunity_service.py"]
                    }
                ]
            }
        elif model_name == "SolutionPlanOutput":
             data = {
                 "problem": "Token expiration not handled in auth service",
                 "implementation_steps": [
                     "Locate the TODO in auth.py",
                     "Implement the token validation logic",
                     "Add unit tests for the new logic"
                 ],
                 "relevant_files": ["backend/app/security/auth.py"],
                 "estimated_complexity": "Low"
             }
        elif model_name == "OpportunityScoreCard":
             data = {
                 "overall_score": 85.0,
                 "impact_score": 90.0,
                 "confidence_score": 95.0,
                 "alignment_score": 80.0,
                 "reasoning": "This is a high impact bug fix with clear evidence."
             }
        else:
            # Fallback for unknown models: try to instantiate with empty/default values
            logger.warning(f"MockAIProvider: No specific mock data for {model_name}. Attempting generic instantiation.")
            try:
                return response_model.model_construct()
            except:
                data = {}

        return response_model.model_validate(data)

    async def generate_embeddings(self, request: EmbeddingsRequest) -> EmbeddingsResponse:
        logger.info("MockAIProvider: Simulating embeddings")
        # Return 768-dimension zero vector (or random)
        dim = 768
        if isinstance(request.input, list):
            embeddings = [[0.0] * dim for _ in request.input]
        else:
            embeddings = [[0.0] * dim]

        return EmbeddingsResponse(
            embeddings=embeddings,
            usage={"total_tokens": 5}
        )
