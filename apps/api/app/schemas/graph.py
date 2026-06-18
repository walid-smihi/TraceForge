import uuid
from typing import Any, Optional

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    node_type: str
    label: str
    sublabel: Optional[str] = None
    data: dict[str, Any]


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    status: str
    confidence_score: Optional[float] = None
    is_manual: bool


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ProjectMetrics(BaseModel):
    project_id: uuid.UUID
    requirements_total: int
    requirements_linked: int
    requirements_unlinked: int
    requirements_ambiguous: int
    coverage_percent: float
    code_files_total: int
    code_files_linked: int
    test_files_total: int
    links_total: int
    links_validated: int
    links_suggested: int
    links_rejected: int
    conflicts_open: int
