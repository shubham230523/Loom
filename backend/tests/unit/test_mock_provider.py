import pytest
from pydantic import BaseModel
from backend.app.ai.providers.mock import MockAIProvider
from backend.app.ai.schemas import ChatRequest, ChatMessage, MessageRole, EmbeddingsRequest

class OpportunityList(BaseModel):
    opportunities: list

class SolutionPlanOutput(BaseModel):
    problem: str
    implementation_steps: list

class OpportunityScoreCard(BaseModel):
    overall_score: float

@pytest.mark.asyncio
async def test_mock_chat():
    provider = MockAIProvider()
    req = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")])
    res = await provider.chat(req)
    assert "mock AI response" in res.message.content

@pytest.mark.asyncio
async def test_mock_chat_stream():
    provider = MockAIProvider()
    req = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")])
    chunks = []
    async for chunk in provider.chat_stream(req):
        chunks.append(chunk)
    assert len(chunks) > 0

@pytest.mark.asyncio
async def test_mock_chat_structured():
    provider = MockAIProvider()
    req = ChatRequest(messages=[ChatMessage(role=MessageRole.USER, content="hi")])

    # 1. OpportunityList
    res = await provider.chat_structured(req, OpportunityList)
    assert len(res.opportunities) == 2

    # 2. SolutionPlanOutput
    res = await provider.chat_structured(req, SolutionPlanOutput)
    assert "Token expiration" in res.problem

    # 3. OpportunityScoreCard
    res = await provider.chat_structured(req, OpportunityScoreCard)
    assert res.overall_score == 85.0

    # 4. Unknown
    class Unknown(BaseModel):
        x: int = 1
    res = await provider.chat_structured(req, Unknown)
    assert res.x == 1

@pytest.mark.asyncio
async def test_mock_embeddings():
    provider = MockAIProvider()
    # String input
    req = EmbeddingsRequest(input="test")
    res = await provider.generate_embeddings(req)
    assert len(res.embeddings) == 1
    assert len(res.embeddings[0]) == 768

    # List input
    req = EmbeddingsRequest(input=["a", "b"])
    res = await provider.generate_embeddings(req)
    assert len(res.embeddings) == 2
