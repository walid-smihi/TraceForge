import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services import job_service
from app.services.project_service import get_project

router = APIRouter(prefix="/projects/{project_id}/export", tags=["export"])


def _render_markdown(report: dict) -> str:
    req = report["requirement"]
    lines = [
        f"# Rapport d'impact — {req['code']}",
        "",
        f"**Exigence :** {req['title']}",
        "",
        f"**Description actuelle :** {req['description'] or '—'}",
        "",
        f"**Modification envisagée :** {report.get('modification_description') or '—'}",
        "",
    ]

    if report.get("summary"):
        lines += ["## Résumé", "", report["summary"], ""]

    lines += [f"## Fichiers directement impactés ({len(report['direct_files'])})", ""]
    if report["direct_files"]:
        for f in report["direct_files"]:
            lines.append(f"- `{f['path']}`" + (f" — {f['summary']}" if f.get("summary") else ""))
    else:
        lines.append("Aucun.")
    lines.append("")

    lines += [f"## Tests directement impactés ({len(report['direct_tests'])})", ""]
    if report["direct_tests"]:
        for f in report["direct_tests"]:
            lines.append(f"- `{f['path']}`")
    else:
        lines.append("Aucun.")
    lines.append("")

    lines += [
        f"## Exigences indirectement impactées ({len(report['indirect_requirements'])})",
        "",
    ]
    if report["indirect_requirements"]:
        for r in report["indirect_requirements"]:
            lines.append(f"- {r['code']} — {r['title']}")
    else:
        lines.append("Aucune.")
    lines.append("")

    lines += [f"## Conflits ouverts ({len(report['conflicts'])})", ""]
    if report["conflicts"]:
        for c in report["conflicts"]:
            lines.append(f"- **{c['rule_id']}** — {c['title']} : {c.get('description') or ''}")
    else:
        lines.append("Aucun.")
    lines.append("")

    return "\n".join(lines)


def _render_pdf(report: dict) -> bytes:
    req = report["requirement"]
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def line(h: float, text: str):
        # multi_cell(w=0, ...) leaves the cursor at the right margin unless
        # explicitly told to wrap back to the left margin on a new line —
        # without this, the next call sees ~0 available width and hangs/fails.
        pdf.multi_cell(0, h, text, wrapmode="CHAR", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 16)
    line(10, f"Rapport d'impact - {req['code']}")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    line(7, f"Exigence : {req['title']}")
    line(7, f"Modification envisagée : {report.get('modification_description') or '-'}")
    pdf.ln(4)

    def section(title: str, items: list[str]):
        pdf.set_font("Helvetica", "B", 13)
        line(8, title)
        pdf.set_font("Helvetica", "", 10)
        if items:
            for item in items:
                line(6, f"- {item}")
        else:
            line(6, "Aucun.")
        pdf.ln(3)

    if report.get("summary"):
        section("Résumé", [report["summary"]])

    section(
        f"Fichiers directement impactés ({len(report['direct_files'])})",
        [f["path"] for f in report["direct_files"]],
    )
    section(
        f"Tests directement impactés ({len(report['direct_tests'])})",
        [f["path"] for f in report["direct_tests"]],
    )
    section(
        f"Exigences indirectement impactées ({len(report['indirect_requirements'])})",
        [f"{r['code']} - {r['title']}" for r in report["indirect_requirements"]],
    )
    section(
        f"Conflits ouverts ({len(report['conflicts'])})",
        [f"{c['rule_id']} - {c['title']}" for c in report["conflicts"]],
    )

    return bytes(pdf.output())


@router.get("/impact/{job_id}")
async def export_impact_report(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    format: str = Query("md", pattern="^(md|pdf)$"),
    session: AsyncSession = Depends(get_session),
):
    project = await get_project(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = await job_service.get_job(session, job_id)
    if not job or job.project_id != project_id or job.job_type != "generate_impact":
        raise HTTPException(status_code=404, detail="Impact report not found")
    if job.status != "completed" or not job.result_data:
        raise HTTPException(status_code=400, detail="Impact report is not ready")

    report = job.result_data
    code = report["requirement"]["code"]

    if format == "md":
        content = _render_markdown(report)
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="impact-{code}.md"'},
        )

    content = _render_pdf(report)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="impact-{code}.pdf"'},
    )
