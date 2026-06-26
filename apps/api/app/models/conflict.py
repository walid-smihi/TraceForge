import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.db_types import UUIDList


class DetectedConflict(Base):
    __tablename__ = "detected_conflicts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    severity: Mapped[str] = mapped_column(String(10), server_default="warning")
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirement_ids: Mapped[Optional[list]] = mapped_column(UUIDList, nullable=True)
    status: Mapped[str] = mapped_column(String(20), server_default="open")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
