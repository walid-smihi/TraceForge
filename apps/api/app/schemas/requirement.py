import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

REQ_TYPES = ("functional", "security", "performance", "availability", "compliance", "interface")
REQ_PRIORITIES = ("critical", "high", "medium", "low")
REQ_STATUSES = ("draft", "active", "modified", "deprecated")


class RequirementCreate(BaseModel):
    title: str
    description: Optional[str] = None
    req_type: str = "functional"
    priority: str = "medium"
    is_ambiguous: bool = False
    ambiguity_reason: Optional[str] = None


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    req_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    is_ambiguous: Optional[bool] = None
    ambiguity_reason: Optional[str] = None


class RequirementResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    code: str
    title: str
    description: Optional[str]
    req_type: str
    priority: str
    status: str
    is_ambiguous: bool
    ambiguity_reason: Optional[str]
    source_document_id: Optional[uuid.UUID]
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
