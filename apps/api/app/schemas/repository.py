import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RepositoryCreate(BaseModel):
    name: str
    local_path: str


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    source_type: str
    local_path: Optional[str]
    status: str
    file_count: int
    test_count: int
    scanned_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class CodeFileResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    project_id: uuid.UUID
    path: str
    language: Optional[str]
    summary: Optional[str]
    role_detected: Optional[str]
    entities: Optional[list[str]]
    is_test_file: bool
    line_count: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}
