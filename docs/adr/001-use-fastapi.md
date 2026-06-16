# ADR-001 — Utiliser FastAPI comme framework backend

**Statut :** Accepté  
**Date :** 2026-06

## Contexte

On a besoin d'un framework Python pour exposer une API REST. Les tâches d'analyse (LLM, embeddings) sont potentiellement lentes → besoin d'async natif. On veut une documentation Swagger auto-générée.

## Décision

FastAPI.

## Raisons

- Async natif (asyncio) → adapté aux appels LLM et DB non-bloquants
- Validation Pydantic intégrée → moins de code de validation manuel
- Swagger UI auto-généré → documentation API gratuite
- Performances benchmarkées comparables à Node.js
- Type hints Python natifs

## Alternatives considérées

- **Django REST Framework** : sync-first, trop lourd pour une API simple, ORM couplé
- **Flask** : pas d'async natif, pas de validation intégrée
- **Litestar** : similaire à FastAPI mais écosystème plus petit

## Conséquences

- SQLAlchemy async pour la DB (légèrement plus complexe que sync)
- Pas de Django admin (non nécessaire pour V1)
