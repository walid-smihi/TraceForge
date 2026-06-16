# ADR-002 — Utiliser PostgreSQL + pgvector

**Statut :** Accepté  
**Date :** 2026-06

## Contexte

On a besoin de stocker des données relationnelles (projets, exigences, liens) ET des embeddings vectoriels pour la recherche sémantique.

## Décision

PostgreSQL 16 avec l'extension pgvector.

## Raisons

- Une seule base de données pour les données relationnelles et vectorielles
- Pas besoin d'un service externe (Qdrant, Chroma, Pinecone)
- Requêtes hybrides possibles : filtrer par `project_id` ET trier par similarité vectorielle
- pgvector est battle-tested et supporté par les hébergeurs majeurs
- Simplifie le Docker Compose (1 service au lieu de 2)

## Alternatives considérées

- **PostgreSQL + Qdrant séparé** : 2 services à gérer, sync complexe entre les deux
- **MongoDB Atlas** : vendor lock-in, coût
- **SQLite + vectra** : pas de support async correct, limité pour la prod

## Conséquences

- Image Docker `pgvector/pgvector:pg16` (inclut l'extension)
- Migration initiale : `CREATE EXTENSION IF NOT EXISTS vector`
- Index HNSW pour les performances (fonctionne sur tables vides, contrairement à IVFFlat)
- Dimension embeddings fixe par colonne : `vector(768)` pour nomic-embed-text
