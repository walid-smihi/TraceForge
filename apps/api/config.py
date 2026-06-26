from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database — a single SQLite file under STORAGE_PATH. No external DB
    # service needed; this is what lets the backend run as a single process
    # (Docker-free local dev, or bundled as a desktop app sidecar).
    DATABASE_URL: str = "sqlite+aiosqlite:////app/storage/traceforge.db"

    # Storage
    STORAGE_PATH: str = "/app/storage"

    # Security
    JWT_SECRET: str = "change-this-in-production-min-32-chars"

    # LLM
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    MISTRAL_API_KEY: str = ""
    MISTRAL_MODEL: str = "mistral-small-latest"

    # App
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"
    MAX_UPLOAD_SIZE_MB: int = 50


settings = Settings()
