import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class JobResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    job_type: str
    status: str
    progress: int
    result_data: Optional[Any]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = {"from_attributes": True}
