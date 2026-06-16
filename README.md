# TraceForge

**Local-first traceability tool** — links requirements → code → tests → tickets and generates impact reports automatically.

[![CI](https://github.com/your-username/traceforge/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/traceforge/actions/workflows/ci.yml)

---

## What it does

When a requirement changes, nobody knows exactly what it impacts in the code. TraceForge fixes that:

1. **Extracts requirements** from PDF/Markdown specs via LLM
2. **Scans your repo** and summarizes each file
3. **Suggests trace links** between requirements and code files via vector similarity (pgvector)
4. **Detects conflicts** (e.g. timeout REQ-A = 4min, max duration REQ-B = 5min → bug in prod)
5. **Generates impact reports** (Markdown/PDF) before merging a PR

All AI suggestions are validated by the user. All data stays local by default (Ollama).

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 + TypeScript + Tailwind + Shadcn/ui |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 + pgvector |
| Queue | Redis 7 + RQ |
| LLM local | Ollama (llama3.1:8b + nomic-embed-text) |
| LLM cloud | OpenAI / Mistral (optional, user key) |
| Deploy | Docker Compose |

---

## 5-minute setup

```bash
git clone https://github.com/your-username/traceforge.git
cd traceforge

cp .env.example .env
# Edit .env if needed (default works for local dev)

make up-no-ollama
# → frontend: http://localhost:3000
# → API docs: http://localhost:8000/docs

# In a second terminal:
make migrate

# Optional: load the DemoShop demo project
make seed-demo

# Optional: pull Ollama models (~5 GB)
make ollama-pull
# Then: make up  (starts with Ollama profile)
```

---

## Demo

The built-in **DemoShop** project demonstrates a real e-commerce bug:
- `reservation.service.ts` sets `RESERVATION_TIMEOUT_MINUTES = 4`
- `REQ-PAY-002` says 3D Secure can take up to 5 minutes
- → TraceForge detects the conflict and generates an impact report

---

## Project structure

```
apps/web/        Next.js frontend
apps/api/        FastAPI backend + RQ worker
docs/            Architecture docs + ADRs
infra/docker/    Nginx config (prod)
storage/         File storage (gitignored, Docker volume)
```

See [docs/setup.md](docs/setup.md) for full setup instructions.
See [docs/adr/](docs/adr/) for architecture decisions.

---

## License

MIT
