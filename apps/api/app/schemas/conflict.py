import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DetectedConflictResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    rule_id: Optional[str] = None
    severity: str
    title: str
    description: Optional[str] = None
    requirement_ids: Optional[list[uuid.UUID]] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ConflictUpdate(BaseModel):
    status: str
