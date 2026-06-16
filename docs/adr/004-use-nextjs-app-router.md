# ADR-004 — Utiliser Next.js App Router + Shadcn/ui

**Statut :** Accepté  
**Date :** 2026-06

## Contexte

On a besoin d'un framework frontend moderne avec TypeScript, un bon écosystème de composants UI, et une intégration naturelle avec React Flow (graphe de traçabilité).

## Décision

Next.js 14+ avec App Router + Shadcn/ui + Tailwind CSS.

## Raisons

- **Next.js App Router** : React Server Components, routing basé sur le système de fichiers, streaming
- **Shadcn/ui** : composants copiés dans le projet (pas de dépendance externe), accessibles, stylisables avec Tailwind
- **Tailwind CSS** : utility-first, facile à customiser, DX excellente
- **React Flow** : librairie de graphe interactif mature, compatible React

## Alternatives considérées

- **Vite + React SPA** : pas de SSR, routing manuel (react-router)
- **Remix** : bon mais moins d'exemples Shadcn/ui
- **Vue.js** : pas de React Flow équivalent aussi mature

## Conséquences

- App Router impose une distinction Server Components / Client Components (`"use client"` explicite)
- Shadcn/ui = composants dans le repo (facile à modifier, mais à maintenir)
- Pas de CSS modules ni de styled-components → uniquement Tailwind
- `"use client"` requis pour React Flow et tous les composants interactifs
