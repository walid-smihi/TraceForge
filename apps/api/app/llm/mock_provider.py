import json
from typing import Any

from app.llm.base import LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    """Used in CI and unit tests — no external calls."""

    async def complete(self, prompt: str, system: str = "", **kwargs: Any) -> LLMResponse:
        mock_content = json.dumps({"requirements": [], "summary": "mock response"})
        return LLMResponse(
            content=mock_content,
            input_tokens=len(prompt) // 4,
            output_tokens=10,
            model="mock",
            provider="mock",
        )

    async def embed(self, text: str) -> list[float]:
        return [0.0] * 768

    async def health_check(self) -> bool:
        return True
