from typing import Optional

from pydantic import BaseModel


class SearchResult(BaseModel):
    type: str
    id: str
    code: str
    title: str
    summary: Optional[str] = None
    score: float
