from backend.app.ai.base import AIProvider
from backend.app.ai.providers.ollama import OllamaCloudProvider
from backend.app.ai.providers.openrouter import OpenRouterProvider
from backend.app.config import settings
from backend.app.api.errors import LoomError

def get_ai_provider() -> AIProvider:
    """
    Factory function to get the configured AI provider.
    """
    if settings.AI_PROVIDER == "ollama-cloud":
        return OllamaCloudProvider()
    elif settings.AI_PROVIDER == "openrouter":
        return OpenRouterProvider()

    # Placeholder for other providers
    raise LoomError(f"AI Provider '{settings.AI_PROVIDER}' not implemented", status_code=500)
