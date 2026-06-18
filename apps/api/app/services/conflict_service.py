import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_file import CodeFile
from app.models.conflict import DetectedConflict
from app.models.requirement import Requirement
from app.models.trace_link import TraceLink

# RULE-002 — domain keywords that must overlap between two requirements
# before their numeric temporal values are considered comparable.
_DOMAIN_WORDS = {
    "paiement",
    "session",
    "réservation",
    "reservation",
    "stock",
    "checkout",
    "validation",
    "panier",
    "authentification",
    "timeout",
    "expiration",
    "délai",
    "delai",
    "scan",
    "job",
    "tâche",
    "tache",
}

_TIME_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(ms|millisecondes?|secondes?|sec\b|s\b|minutes?|min\b|heures?|h\b)",
    re.IGNORECASE,
)

_UNIT_TO_SECONDS = {
    "ms": 0.001,
    "millisecond": 0.001,
    "milliseconde": 0.001,
    "millisecondes": 0.001,
    "s": 1,
    "sec": 1,
    "seconde": 1,
    "secondes": 1,
    "min": 60,
    "minute": 60,
    "minutes": 60,
    "h": 3600,
    "heure": 3600,
    "heures": 3600,
}


def _extract_time_values(text: str) -> list[tuple[float, str]]:
    """Return (value_in_seconds, raw_match) for every temporal value found."""
    results = []
    for match in _TIME_PATTERN.finditer(text):
        raw_value, raw_unit = match.groups()
        value = float(raw_value.replace(",", "."))
        unit_key = raw_unit.lower().rstrip(".")
        seconds = _UNIT_TO_SECONDS.get(unit_key)
        if seconds is None:
            continue
        results.append((value * seconds, match.group(0)))
    return results


def _shared_domain_words(text_a: str, text_b: str) -> set[str]:
    words_a = {w.lower() for w in re.findall(r"\w+", text_a)}
    words_b = {w.lower() for w in re.findall(r"\w+", text_b)}
    return (words_a & words_b) & _DOMAIN_WORDS


async def _detect_rule_001_006(
    session: AsyncSession,
    project_id: uuid.UUID,
    reqs: list[Requirement],
    links: list[TraceLink],
    files_by_id: dict[uuid.UUID, CodeFile],
    rule_id: str,
    req_filter,
    title_template: str,
) -> list[DetectedConflict]:
    validated_test_targets: dict[uuid.UUID, set[uuid.UUID]] = {}
    for link in links:
        if (
            link.source_type == "requirement"
            and link.target_type == "code_file"
            and link.status == "validated"
        ):
            target_file = files_by_id.get(link.target_id)
            if target_file and target_file.is_test_file:
                validated_test_targets.setdefault(link.source_id, set()).add(link.target_id)

    conflicts = []
    for req in reqs:
        if not req_filter(req):
            continue
        if validated_test_targets.get(req.id):
            continue
        conflicts.append(
            DetectedConflict(
                project_id=project_id,
                rule_id=rule_id,
                severity="critical",
                title=title_template.format(code=req.code),
                description=f"L'exigence {req.code} ({req.title}) n'a aucun test validé associé.",
                requirement_ids=[req.id],
            )
        )
    return conflicts


async def _detect_rule_002(
    project_id: uuid.UUID, reqs: list[Requirement]
) -> list[DetectedConflict]:
    extracted = []
    for req in reqs:
        text = f"{req.title} {req.description or ''}"
        values = _extract_time_values(text)
        if values:
            extracted.append((req, text, values))

    conflicts = []
    seen_pairs = set()
    for i, (req_a, text_a, values_a) in enumerate(extracted):
        for req_b, text_b, values_b in extracted[i + 1 :]:
            pair_key = tuple(sorted((req_a.id, req_b.id)))
            if pair_key in seen_pairs:
                continue
            shared = _shared_domain_words(text_a, text_b)
            if not shared:
                continue

            max_a = max(v for v, _ in values_a)
            max_b = max(v for v, _ in values_b)
            if max_a == max_b:
                continue

            seen_pairs.add(pair_key)
            raw_a = max((v, r) for v, r in values_a)[1]
            raw_b = max((v, r) for v, r in values_b)[1]
            conflicts.append(
                DetectedConflict(
                    project_id=project_id,
                    rule_id="RULE-002",
                    severity="critical",
                    title=f"Conflit potentiel de durée entre {req_a.code} et {req_b.code}",
                    description=(
                        f"{req_a.code} mentionne « {raw_a} » et {req_b.code} mentionne « {raw_b} » "
                        f"dans un contexte partagé ({', '.join(sorted(shared))}). "
                        "Vérifiez que ces durées restent compatibles."
                    ),
                    requirement_ids=[req_a.id, req_b.id],
                )
            )
    return conflicts


async def detect_conflicts(session: AsyncSession, project_id: uuid.UUID) -> int:
    """Run all conflict-detection rules for a project. Returns the number of open conflicts created."""
    reqs_result = await session.execute(
        select(Requirement).where(Requirement.project_id == project_id)
    )
    reqs = list(reqs_result.scalars().all())

    files_result = await session.execute(select(CodeFile).where(CodeFile.project_id == project_id))
    files_by_id = {f.id: f for f in files_result.scalars().all()}

    links_result = await session.execute(
        select(TraceLink).where(TraceLink.project_id == project_id)
    )
    links = list(links_result.scalars().all())

    # Clear previously auto-detected open conflicts before recomputing.
    existing_result = await session.execute(
        select(DetectedConflict).where(
            DetectedConflict.project_id == project_id,
            DetectedConflict.status == "open",
        )
    )
    for conflict in existing_result.scalars().all():
        await session.delete(conflict)
    await session.flush()

    new_conflicts: list[DetectedConflict] = []
    new_conflicts += await _detect_rule_001_006(
        session,
        project_id,
        reqs,
        links,
        files_by_id,
        rule_id="RULE-001",
        req_filter=lambda r: r.priority == "critical",
        title_template="{code} critique sans test validé",
    )
    new_conflicts += await _detect_rule_001_006(
        session,
        project_id,
        reqs,
        links,
        files_by_id,
        rule_id="RULE-006",
        req_filter=lambda r: r.req_type == "security",
        title_template="{code} de sécurité sans test validé",
    )
    new_conflicts += await _detect_rule_002(project_id, reqs)

    for conflict in new_conflicts:
        session.add(conflict)
    await session.commit()

    return len(new_conflicts)
