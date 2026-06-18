import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_file import CodeFile
from app.models.conflict import DetectedConflict
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse, ProjectMetrics


def _req_node_id(req_id: uuid.UUID) -> str:
    return f"requirement:{req_id}"


def _file_node_id(file_id: uuid.UUID) -> str:
    return f"code_file:{file_id}"


async def build_graph(session: AsyncSession, project_id: uuid.UUID) -> GraphResponse:
    reqs_result = await session.execute(
        select(Requirement).where(Requirement.project_id == project_id)
    )
    reqs = list(reqs_result.scalars().all())

    files_result = await session.execute(select(CodeFile).where(CodeFile.project_id == project_id))
    files = list(files_result.scalars().all())

    links_result = await session.execute(
        select(TraceLink).where(TraceLink.project_id == project_id)
    )
    links = list(links_result.scalars().all())

    linked_req_ids = {link.source_id for link in links if link.source_type == "requirement"}
    linked_file_ids = {link.target_id for link in links if link.target_type == "code_file"}

    nodes: list[GraphNode] = []
    for req in reqs:
        nodes.append(
            GraphNode(
                id=_req_node_id(req.id),
                node_type="requirement",
                label=req.title,
                sublabel=req.code,
                data={
                    "id": str(req.id),
                    "code": req.code,
                    "title": req.title,
                    "description": req.description,
                    "req_type": req.req_type,
                    "priority": req.priority,
                    "status": req.status,
                    "is_ambiguous": req.is_ambiguous,
                    "ambiguity_reason": req.ambiguity_reason,
                    "is_linked": req.id in linked_req_ids,
                },
            )
        )

    for f in files:
        nodes.append(
            GraphNode(
                id=_file_node_id(f.id),
                node_type="code_file",
                label=f.path.rsplit("/", 1)[-1],
                sublabel=f.language,
                data={
                    "id": str(f.id),
                    "path": f.path,
                    "language": f.language,
                    "summary": f.summary,
                    "role_detected": f.role_detected,
                    "is_test_file": f.is_test_file,
                    "is_linked": f.id in linked_file_ids,
                },
            )
        )

    edges = [
        GraphEdge(
            id=str(link.id),
            source=_req_node_id(link.source_id),
            target=_file_node_id(link.target_id),
            status=link.status,
            confidence_score=float(link.confidence_score) if link.confidence_score else None,
            is_manual=link.is_manual,
        )
        for link in links
        if link.source_type == "requirement" and link.target_type == "code_file"
    ]

    return GraphResponse(nodes=nodes, edges=edges)


async def get_metrics(session: AsyncSession, project_id: uuid.UUID) -> ProjectMetrics:
    reqs_result = await session.execute(
        select(Requirement).where(Requirement.project_id == project_id)
    )
    reqs = list(reqs_result.scalars().all())

    files_result = await session.execute(select(CodeFile).where(CodeFile.project_id == project_id))
    files = list(files_result.scalars().all())

    links_result = await session.execute(
        select(TraceLink).where(TraceLink.project_id == project_id)
    )
    links = list(links_result.scalars().all())

    conflicts_result = await session.execute(
        select(DetectedConflict).where(
            DetectedConflict.project_id == project_id,
            DetectedConflict.status == "open",
        )
    )
    conflicts = list(conflicts_result.scalars().all())

    linked_req_ids = {
        link.source_id
        for link in links
        if link.source_type == "requirement" and link.status != "rejected"
    }
    linked_file_ids = {
        link.target_id
        for link in links
        if link.target_type == "code_file" and link.status != "rejected"
    }

    requirements_total = len(reqs)
    requirements_linked = len([r for r in reqs if r.id in linked_req_ids])

    return ProjectMetrics(
        project_id=project_id,
        requirements_total=requirements_total,
        requirements_linked=requirements_linked,
        requirements_unlinked=requirements_total - requirements_linked,
        requirements_ambiguous=len([r for r in reqs if r.is_ambiguous]),
        coverage_percent=round(100 * requirements_linked / requirements_total, 1)
        if requirements_total
        else 0.0,
        code_files_total=len(files),
        code_files_linked=len([f for f in files if f.id in linked_file_ids]),
        test_files_total=len([f for f in files if f.is_test_file]),
        links_total=len(links),
        links_validated=len([link for link in links if link.status == "validated"]),
        links_suggested=len([link for link in links if link.status == "suggested"]),
        links_rejected=len([link for link in links if link.status == "rejected"]),
        conflicts_open=len(conflicts),
    )
