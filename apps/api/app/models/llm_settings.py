import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LLMSettings(Base):
    __tablename__ = "llm_settings"

    id: Mapped[uuid.UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(20), server_default="ollama", nullable=False)
    ollama_base_url: Mapped[Optional[str]] = mapped_column(Text, server_default="http://ollama:11434")
    ollama_model: Mapped[Optional[str]] = mapped_column(String(100), server_default="llama3.1:8b")
    ollama_embed_model: Mapped[Optional[str]] = mapped_column(String(100), server_default="nomic-embed-text")
    openai_api_key_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    openai_model: Mapped[Optional[str]] = mapped_column(String(100), server_default="gpt-4o-mini")
    mistral_api_key_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mistral_model: Mapped[Optional[str]] = mapped_column(String(100), server_default="mistral-small-latest")
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
