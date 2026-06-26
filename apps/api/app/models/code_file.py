import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import EmbeddingVector


class CodeRepository(Base):
    __tablename__ = "code_repositories"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    local_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    scanned_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    file_count: Mapped[int] = mapped_column(Integer, server_default="0")
    test_count: Mapped[int] = mapped_column(Integer, server_default="0")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class CodeFile(Base):
    __tablename__ = "code_files"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("code_repositories.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_detected: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entities: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    constants: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_test_file: Mapped[bool] = mapped_column(Boolean, server_default="false")
    line_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    embedding: Mapped[Optional[list]] = mapped_column(EmbeddingVector, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
