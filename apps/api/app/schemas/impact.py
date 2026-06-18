import uuid

from pydantic import BaseModel


class ImpactAnalyzeRequest(BaseModel):
    requirement_id: uuid.UUID
    modification_description: str
