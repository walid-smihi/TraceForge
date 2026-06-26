import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import EmbeddingVector


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    req_type: Mapped[str] = mapped_column(String(50), server_default="functional", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), server_default="medium")
    status: Mapped[str] = mapped_column(String(20), server_default="draft")
    is_ambiguous: Mapped[bool] = mapped_column(Boolean, server_default="false")
    ambiguity_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("documents.id"), nullable=True
    )
    source_chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("document_chunks.id"), nullable=True
    )
    embedding: Mapped[Optional[list]] = mapped_column(EmbeddingVector, nullable=True)
    version: Mapped[int] = mapped_column(Integer, server_default="1")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
