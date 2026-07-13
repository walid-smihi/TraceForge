# TraceForge

**Local-first requirements traceability tool** — links requirements → code → tests, detects conflicts, and generates impact reports. Runs entirely on your machine, no cloud required.

[![CI](https://github.com/walid-smihi/TraceForge/actions/workflows/ci.yml/badge.svg)](https://github.com/walid-smihi/TraceForge/actions/workflows/ci.yml)

---

## What it does

When a requirement changes, nobody knows exactly what it impacts in the code. TraceForge fixes that:

1. **Extracts requirements** from PDF/Markdown/DOCX specs via LLM
2. **Scans your repo** and summarizes each file
3. **Suggests trace links** between requirements and code files via vector similarity
4. **Detects conflicts** (e.g. timeout REQ-A = 4 min, max duration REQ-B = 5 min → bug in prod)
5. **Generates impact reports** (Markdown/PDF) before merging a PR

All AI suggestions are validated by the user. All data stays local (Ollama).

---

## Two ways to run it

### Option A — Desktop app (recommended)

Download the installer for your OS, double-click, done. No Docker, no terminal, no server.

| Platform | File |
|---|---|
| Linux | `TraceForge_0.1.0_amd64.AppImage` or `.deb` |
| Windows / macOS | _coming soon_ |

**Requirements:** [Ollama](https://ollama.com) installed and running locally.

```bash
# Pull the models once (≈ 5 GB)
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

Git must also be installed on your machine to use the repository import feature.

---

### Option B — Docker Compose (web)

```bash
git clone https://github.com/walid-smihi/TraceForge.git
cd TraceForge

cp .env.example .env

docker compose up -d
# → frontend: http://localhost:3000
# → API docs:  http://localhost:8000/docs

# Pull Ollama models (first time only, ≈ 5 GB)
docker compose exec ollama ollama pull llama3.1:8b
docker compose exec ollama ollama pull nomic-embed-text
```

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 + TypeScript + Tailwind + shadcn/ui |
| Backend | FastAPI (Python 3.12) + asyncio background tasks |
| Database | SQLite (via aiosqlite) — no external DB service |
| LLM local | Ollama (llama3.1:8b + nomic-embed-text) |
| LLM cloud | OpenAI / Mistral (optional, user key) |
| Desktop | Tauri v2 + PyInstaller sidecar |
| Web deploy | Docker Compose |

---

## Project structure

```
apps/
  web/        Next.js frontend (static export for desktop, standalone for web)
  api/        FastAPI backend (SQLite, asyncio tasks, Ollama)
  desktop/    Tauri shell — wraps the frontend + bundles the backend as a sidecar
docs/         Architecture docs + ADRs
infra/        Nginx config (prod)
storage/      File storage (gitignored)
```

---

## Architecture decisions

| ADR | Decision |
|---|---|
| [001](docs/adr/001-use-fastapi.md) | FastAPI for the backend |
| [002](docs/adr/002-use-postgresql-pgvector.md) | SQLite replaces PostgreSQL (desktop migration) |
| [003](docs/adr/003-local-first-llm.md) | Ollama local-first, cloud optional |
| [004](docs/adr/004-use-nextjs-app-router.md) | Next.js App Router |
| [005](docs/adr/005-no-auth-v1.md) | No auth in V1 |

---

## Building the desktop app from source

```bash
# 1. Build the Python sidecar
cd apps/api
bash build_sidecar.sh        # requires rustc + pyinstaller deps

# 2. Build the Tauri app
cd apps/desktop
npm install
npm run tauri build          # outputs AppImage / .deb / .rpm in src-tauri/target/release/bundle/
```

---

## License

MIT
