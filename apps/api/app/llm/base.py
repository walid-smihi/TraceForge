from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str = "", **kwargs: Any) -> LLMResponse:
        """Send a completion request and return the response."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable."""
