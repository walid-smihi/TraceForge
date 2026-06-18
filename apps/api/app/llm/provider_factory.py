import logging

from app.llm.base import LLMProvider
from app.llm.mock_provider import MockProvider

logger = logging.getLogger(__name__)


def get_provider() -> LLMProvider:
    from config import settings

    match settings.LLM_PROVIDER.lower():
        case "mock":
            return MockProvider()
        case "ollama":
            from app.llm.ollama_provider import OllamaProvider

            return OllamaProvider(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                embed_model=settings.OLLAMA_EMBED_MODEL,
            )
        case "openai":
            from app.llm.openai_provider import OpenAIProvider

            return OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
            )
        case _:
            logger.warning(
                "Unknown LLM_PROVIDER=%s, falling back to MockProvider", settings.LLM_PROVIDER
            )
            return MockProvider()
