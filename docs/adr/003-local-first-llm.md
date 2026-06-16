# ADR-003 — Stratégie LLM local-first avec Ollama

**Statut :** Accepté  
**Date :** 2026-06

## Contexte

L'application analyse des documents de spécification qui peuvent contenir des informations confidentielles (spécifications techniques, propriété intellectuelle).

## Décision

Ollama local comme provider LLM par défaut. Providers cloud (OpenAI, Mistral) optionnels et nécessitant une clé utilisateur.

## Raisons

- **Confidentialité** : les données ne quittent pas la machine de l'utilisateur par défaut
- **Coût** : $0 de coût API en mode local
- **Mode offline** : fonctionne sans connexion internet
- Adapté au persona cible (Amira, tech lead qui ne veut pas envoyer les specs hors de l'entreprise)

## Alternatives considérées

- **OpenAI only** : meilleure qualité mais coût et confidentialité problématiques
- **API propriétaire hébergée** : complexité déploiement, coût serveur GPU

## Conséquences

- Performance LLM inférieure au GPT-4 sur CPU (~10x plus lent)
- Nécessite un téléchargement initial des modèles (~5 GB pour llama3.1:8b)
- Interface `LLMProvider` abstraite pour changer de provider sans toucher au code métier
- `MockProvider` pour la CI (pas d'Ollama sur les runners GitHub Actions)

## Modèles par défaut

| Usage | Modèle | Taille |
|---|---|---|
| Texte / extraction | `llama3.1:8b` | ~4.7 GB |
| Embeddings | `nomic-embed-text` | ~274 MB |
