import json
from typing import Any

from app.llm.base import LLMProvider, LLMResponse

MOCK_REQUIREMENTS = [
    {
        "title": "Créer un projet avec nom et description",
        "description": "L'utilisateur doit pouvoir créer un projet en fournissant un nom, une description optionnelle et un domaine métier.",
        "type": "functional",
        "priority": "critical",
        "is_ambiguous": False,
        "ambiguity_reason": None,
    },
    {
        "title": "Uploader un document de spécification",
        "description": "Le système doit accepter les fichiers PDF, DOCX et Markdown jusqu'à 50 MB.",
        "type": "functional",
        "priority": "critical",
        "is_ambiguous": False,
        "ambiguity_reason": None,
    },
    {
        "title": "Extraire les exigences via LLM",
        "description": "Le système doit extraire automatiquement les exigences présentes dans un document uploadé en utilisant un modèle de langage.",
        "type": "functional",
        "priority": "critical",
        "is_ambiguous": False,
        "ambiguity_reason": None,
    },
    {
        "title": "Fonctionner entièrement en local",
        "description": "L'application doit fonctionner sans connexion internet avec Ollama local.",
        "type": "availability",
        "priority": "critical",
        "is_ambiguous": False,
        "ambiguity_reason": None,
    },
    {
        "title": "Temps de réponse rapide",
        "description": "Le système doit être performant et réactif.",
        "type": "performance",
        "priority": "medium",
        "is_ambiguous": True,
        "ambiguity_reason": "Aucun seuil numérique défini (ms, RPS, etc.)",
    },
    {
        "title": "Ne pas envoyer de données à l'extérieur",
        "description": "En mode Ollama, aucune donnée ne doit être transmise à des services externes.",
        "type": "security",
        "priority": "critical",
        "is_ambiguous": False,
        "ambiguity_reason": None,
    },
]


class MockProvider(LLMProvider):
    """Used in CI and unit tests — no external calls."""

    async def complete(self, prompt: str, system: str = "", **kwargs: Any) -> LLMResponse:
        mock_content = json.dumps({"requirements": MOCK_REQUIREMENTS})
        return LLMResponse(
            content=mock_content,
            input_tokens=len(prompt) // 4,
            output_tokens=len(mock_content) // 4,
            model="mock",
            provider="mock",
        )

    async def embed(self, text: str) -> list[float]:
        return [0.0] * 768

    async def health_check(self) -> bool:
        return True
