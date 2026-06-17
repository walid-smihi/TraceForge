import json
import logging
from typing import Any

import httpx

from app.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str, model: str, embed_model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.embed_model = embed_model
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=300.0))

    async def complete(self, prompt: str, system: str = "", **kwargs: Any) -> LLMResponse:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "format": "json",
            "options": {"num_predict": 2048, "temperature": 0.1},
        }
        resp = await self._client.post(f"{self.base_url}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("response", "")
        return LLMResponse(
            content=content,
            input_tokens=data.get("prompt_eval_count", len(prompt) // 4),
            output_tokens=data.get("eval_count", len(content) // 4),
            model=self.model,
            provider="ollama",
        )

    async def embed(self, text: str) -> list[float]:
        resp = await self._client.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.embed_model, "prompt": text},
        )
        resp.raise_for_status()
        return resp.json()["embedding"]

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False
