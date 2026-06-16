import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    file_type: str
    file_size_bytes: Optional[int]
    status: str
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    section_title: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
