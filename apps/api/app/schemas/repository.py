import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator

_GITHUB_URL_PATTERN = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+(?:\.git)?/?$")


class RepositoryCreate(BaseModel):
    name: str
    local_path: Optional[str] = None
    github_url: Optional[str] = None

    @model_validator(mode="after")
    def _validate_source(self) -> "RepositoryCreate":
        if bool(self.local_path) == bool(self.github_url):
            raise ValueError("Provide exactly one of local_path or github_url")
        if self.github_url and not _GITHUB_URL_PATTERN.match(self.github_url):
            raise ValueError("github_url must look like https://github.com/<owner>/<repo>")
        return self


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    source_type: str
    source_url: Optional[str] = None
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
