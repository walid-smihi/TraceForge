import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_file import CodeFile
from app.models.conflict import DetectedConflict
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink


async def build_impact_report(
    session: AsyncSession, project_id: uuid.UUID, requirement_id: uuid.UUID
) -> dict:
    requirement = await session.get(Requirement, requirement_id)
    if not requirement or requirement.project_id != project_id:
        raise ValueError("Requirement not found in this project")

    links_result = await session.execute(
        select(TraceLink).where(
            TraceLink.project_id == project_id,
            TraceLink.status != "rejected",
        )
    )
    links = list(links_result.scalars().all())

    # Depth 1 — files directly linked to the requirement being modified.
    direct_file_ids = {
        link.target_id
        for link in links
        if link.source_type == "requirement"
        and link.source_id == requirement_id
        and link.target_type == "code_file"
    }

    # Depth 2 — other requirements that share at least one of those files.
    indirect_req_ids: set[uuid.UUID] = set()
    for link in links:
        if (
            link.target_type == "code_file"
            and link.target_id in direct_file_ids
            and link.source_type == "requirement"
            and link.source_id != requirement_id
        ):
            indirect_req_ids.add(link.source_id)

    file_ids_to_fetch = set(direct_file_ids)
    files_result = await session.execute(select(CodeFile).where(CodeFile.id.in_(file_ids_to_fetch)))
    files_by_id = {f.id: f for f in files_result.scalars().all()}

    direct_files = [files_by_id[fid] for fid in direct_file_ids if fid in files_by_id]
    direct_tests = [f for f in direct_files if f.is_test_file]
    direct_code_files = [f for f in direct_files if not f.is_test_file]

    indirect_reqs: list[Requirement] = []
    if indirect_req_ids:
        indirect_result = await session.execute(
            select(Requirement).where(Requirement.id.in_(indirect_req_ids))
        )
        indirect_reqs = list(indirect_result.scalars().all())

    conflicts_result = await session.execute(
        select(DetectedConflict).where(
            DetectedConflict.project_id == project_id,
            DetectedConflict.status == "open",
        )
    )
    related_conflicts = [
        c
        for c in conflicts_result.scalars().all()
        if c.requirement_ids and requirement_id in c.requirement_ids
    ]

    return {
        "requirement": {
            "id": str(requirement.id),
            "code": requirement.code,
            "title": requirement.title,
            "description": requirement.description,
        },
        "direct_files": [
            {"path": f.path, "language": f.language, "summary": f.summary}
            for f in direct_code_files
        ],
        "direct_tests": [{"path": f.path, "language": f.language} for f in direct_tests],
        "indirect_requirements": [{"code": r.code, "title": r.title} for r in indirect_reqs],
        "conflicts": [
            {"rule_id": c.rule_id, "title": c.title, "description": c.description}
            for c in related_conflicts
        ],
    }
