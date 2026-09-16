import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.app.ai.gateway import AIGateway
from backend.app.ai.schemas import ChatRequest, ChatMessage, MessageRole
from backend.app.ai.providers.mock import MockAIProvider
from backend.app.services.redis import redis_service
from backend.app.config import settings

async def test_cache():
    # Enable cache in settings
    settings.ENABLE_AI_CACHE = True

    print("Connecting to Redis...")
    await redis_service.connect()
    if not redis_service.client:
        print("Redis not available. Skipping test.")
        return

    # Initialize a NEW gateway with the Mock provider
    mock_gateway = AIGateway(provider=MockAIProvider())

    request = ChatRequest(
        messages=[ChatMessage(role=MessageRole.USER, content="Hello, cache test!")],
        model="test-model"
    )

    print("\n--- First Call (Should be MISS) ---")
    start = asyncio.get_event_loop().time()
    resp1 = await mock_gateway.chat(request)
    duration1 = asyncio.get_event_loop().time() - start
    print(f"Response: {resp1.message.content}")
    print(f"Duration: {duration1:.4f}s")

    print("\n--- Second Call (Should be HIT) ---")
    start = asyncio.get_event_loop().time()
    resp2 = await mock_gateway.chat(request)
    duration2 = asyncio.get_event_loop().time() - start
    print(f"Response: {resp2.message.content}")
    print(f"Duration: {duration2:.4f}s")

    if duration2 < duration1 and resp1.message.content == resp2.message.content:
        print("\nSUCCESS: AI Caching is working!")
    else:
        print("\nFAILURE: Caching did not work as expected.")

    await redis_service.disconnect()

if __name__ == "__main__":
    asyncio.run(test_cache())
