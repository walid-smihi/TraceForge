# ADR-005 — Pas d'authentification en V1

**Statut :** Accepté  
**Date :** 2026-06

## Contexte

V1 est un outil local-first mono-utilisateur. Ajouter l'authentification représente ~2 semaines de développement supplémentaires (hash passwords, JWT, sessions, refresh tokens, formulaires login/signup).

## Décision

Aucune authentification en V1. L'app tourne sur localhost uniquement, accessible uniquement à l'utilisateur local.

## Raisons

- Réduction du scope V1 de 2 semaines
- Un seul utilisateur : pas de besoin d'isolation entre comptes
- Sécurité suffisante : localhost non accessible de l'extérieur
- Focus sur les fonctionnalités métier (traçabilité, graphe, impact)

## Conséquences

- L'API n'a pas de middleware d'authentification en V1
- Pas de table `users` en V1 (ajoutée en V2)
- Avant tout déploiement sur staging/prod public : ajouter l'auth (V2)
- Les clés API LLM sont protégées par la sécurité du poste local uniquement en V1

## Plan V2

- Table `users` (id, email, hashed_password, created_at)
- `POST /auth/login` → retourne JWT
- Middleware FastAPI pour valider le JWT sur toutes les routes
- Formulaire login côté Next.js
- Utilisateur unique configuré via `.env` ou premier lancement
