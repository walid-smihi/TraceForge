# Setup — TraceForge

## Prérequis

- Docker >= 24
- Docker Compose >= 2.20
- Git >= 2.40
- (optionnel) Node.js >= 20 pour le dev frontend sans Docker
- (optionnel) Python >= 3.12 pour le dev backend sans Docker

## Lancement en 5 minutes

```bash
# 1. Cloner le repo
git clone https://github.com/your-username/traceforge.git
cd traceforge

# 2. Copier l'env
cp .env.example .env
# Éditez .env si besoin (les valeurs par défaut fonctionnent en local)

# 3. Démarrer les services (sans Ollama pour aller vite)
make up-no-ollama

# 4. Lancer les migrations (dans un 2e terminal)
make migrate

# 5. Accès
# Frontend : http://localhost:3000
# API docs : http://localhost:8000/docs
```

## Avec Ollama (LLM local)

```bash
# Démarrer avec le service Ollama
make up

# Télécharger les modèles (~5 GB)
make ollama-pull
```

## Charger le dataset de démo

```bash
make seed-demo
# Charge le projet DemoShop avec données pré-calculées
# Pas besoin d'Ollama pour la démo (résultats pré-calculés)
```

## Développement local (sans Docker)

### Backend

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Démarrer postgres et redis via Docker
docker compose up -d postgres redis

cp ../../.env.example .env
# Modifier DATABASE_URL pour pointer vers localhost:5432

alembic upgrade head
uvicorn main:app --reload
```

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://...` | URL PostgreSQL |
| `REDIS_URL` | `redis://redis:6379/0` | URL Redis |
| `STORAGE_PATH` | `/app/storage` | Dossier des fichiers uploadés |
| `LLM_PROVIDER` | `ollama` | `ollama` / `openai` / `mistral` / `mock` |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | URL Ollama |
| `OPENAI_API_KEY` | *(vide)* | Clé API OpenAI (optionnel) |
| `APP_ENV` | `development` | `development` / `production` |
| `CORS_ORIGINS` | `http://localhost:3000` | Origines CORS autorisées |

## Commandes utiles

```bash
make test        # Lance tous les tests
make lint        # ESLint + ruff
make format      # Prettier + ruff format
make typecheck   # tsc + mypy
make migrate     # Appliquer les migrations
make db-reset    # Supprimer et recréer la DB (⚠ supprime les données)
```
