.PHONY: up up-no-ollama down logs migrate migration db-reset \
        install-web install-api test test-api test-web \
        lint format typecheck ollama-pull seed-demo

# ── Services ────────────────────────────────────────────────────────────────

up:
	docker compose --profile ollama up --build

up-no-ollama:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

# ── Database ─────────────────────────────────────────────────────────────────

migrate:
	docker compose exec backend alembic upgrade head

migration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

db-reset:
	docker compose down -v
	docker compose up -d postgres redis
	sleep 3
	docker compose exec backend alembic upgrade head

# ── Dev install (local, sans Docker) ─────────────────────────────────────────

install-web:
	cd apps/web && npm install

install-api:
	cd apps/api && pip install -r requirements.txt -r requirements-dev.txt

# ── Tests ────────────────────────────────────────────────────────────────────

test: test-api test-web

test-api:
	docker compose exec backend pytest --cov=app --cov-report=term-missing

test-web:
	cd apps/web && npm test -- --run

# ── Qualité code ─────────────────────────────────────────────────────────────

lint:
	cd apps/api && ruff check .
	cd apps/web && npm run lint

format:
	cd apps/api && ruff format .
	cd apps/web && npx prettier --write .

typecheck:
	cd apps/api && mypy app
	cd apps/web && npm run type-check

# ── Ollama ────────────────────────────────────────────────────────────────────

ollama-pull:
	docker compose exec ollama ollama pull llama3.1:8b
	docker compose exec ollama ollama pull nomic-embed-text

# ── Démo ─────────────────────────────────────────────────────────────────────

seed-demo:
	docker compose exec backend python -m scripts.seed_demo
