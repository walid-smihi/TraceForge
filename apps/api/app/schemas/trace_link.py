import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TraceLinkResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    source_type: str
    source_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    link_type: str
    confidence_score: Optional[float] = None
    status: str
    justification: Optional[str] = None
    is_manual: bool
    created_at: datetime
    requirement_code: Optional[str] = None
    requirement_title: Optional[str] = None
    file_path: Optional[str] = None
    file_language: Optional[str] = None
    file_summary: Optional[str] = None

    model_config = {"from_attributes": True}


class TraceLinkUpdate(BaseModel):
    status: str
    validation_note: Optional[str] = None
