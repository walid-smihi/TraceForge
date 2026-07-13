import asyncio
import hashlib
import json
import logging
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from app.database import async_session_factory
from app.llm.prompts import SUMMARIZE_FILE_PROMPT, SUMMARIZE_FILE_SYSTEM
from app.llm.provider_factory import get_provider
from app.models.analysis_job import AnalysisJob
from app.models.code_file import CodeFile, CodeRepository
from config import settings

logger = logging.getLogger(__name__)

CLONE_TIMEOUT = 120


def _clone_github_repo(url: str, project_id: uuid.UUID, repo_id: uuid.UUID) -> Path:
    dest = Path(settings.STORAGE_PATH) / str(project_id) / "repos" / str(repo_id)
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(dest)],
            capture_output=True,
            text=True,
            timeout=CLONE_TIMEOUT,
        )
    except FileNotFoundError:
        raise ValueError(
            "La commande `git` est introuvable. "
            "Installez Git (https://git-scm.com) pour utiliser l'import de dépôts."
        )
    if result.returncode != 0:
        raise ValueError(f"git clone failed for {url}: {result.stderr.strip()}")
    return dest


LANGUAGE_MAP = {
    "ts": "TypeScript",
    "tsx": "TypeScript",
    "js": "JavaScript",
    "jsx": "JavaScript",
    "mjs": "JavaScript",
    "py": "Python",
    "java": "Java",
    "go": "Go",
    "rs": "Rust",
    "cs": "C#",
    "cpp": "C++",
    "cc": "C++",
    "cxx": "C++",
    "c": "C",
    "rb": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kt": "Kotlin",
    "scala": "Scala",
    "sql": "SQL",
    "sh": "Shell",
    "bash": "Shell",
    "yaml": "YAML",
    "yml": "YAML",
    "json": "JSON",
    "md": "Markdown",
    "html": "HTML",
    "css": "CSS",
    "scss": "CSS",
}

SKIP_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".next",
    "dist",
    "build",
    ".venv",
    "venv",
    "env",
    ".env",
    "coverage",
    ".cache",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".turbo",
    "out",
    "target",
    ".idea",
    ".vscode",
}

SKIP_EXTENSIONS = {
    "lock",
    "min.js",
    "min.css",
    "map",
    "pyc",
    "pyo",
    "class",
    "jar",
    "war",
    "exe",
    "dll",
    "so",
    "dylib",
    "ico",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "svg",
    "woff",
    "woff2",
    "ttf",
    "eot",
    "pdf",
    "zip",
    "tar",
    "gz",
}

TEST_PATTERNS = (
    ".test.",
    ".spec.",
    "_test.",
    "_spec.",
    "/tests/",
    "/test/",
    "/__tests__/",
)


def _detect_test(path: str) -> bool:
    p = path.lower()
    return any(pat in p for pat in TEST_PATTERNS) or Path(path).name.startswith("test_")


def _collect_files(root: Path) -> list[Path]:
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        ext = p.suffix.lstrip(".")
        if ext in SKIP_EXTENSIONS or not ext:
            continue
        if ext not in LANGUAGE_MAP:
            continue
        files.append(p)
    return files


async def _scan_repository(job_id: uuid.UUID, repo_id: uuid.UUID, project_id: uuid.UUID) -> None:
    async with async_session_factory() as session:
        job = await session.get(AnalysisJob, job_id)
        repo = await session.get(CodeRepository, repo_id)
        if not job or not repo:
            return

        job.status = "running"
        job.started_at = datetime.utcnow()
        await session.commit()

        try:
            if repo.source_type == "github":
                # subprocess.run blocks — offload to a thread so it doesn't
                # freeze the event loop now that this runs in-process.
                root = await asyncio.to_thread(
                    _clone_github_repo, repo.source_url, project_id, repo_id
                )
            else:
                root = Path(repo.local_path)
                if not root.exists() or not root.is_dir():
                    raise ValueError(
                        f"Path does not exist or is not a directory: {repo.local_path}"
                    )

            job.progress = 5
            await session.commit()

            files = _collect_files(root)
            total = len(files)
            logger.info("Found %d code files in %s", total, root)

            if total == 0:
                repo.status = "scanned"
                repo.scanned_at = datetime.utcnow()
                repo.file_count = 0
                repo.test_count = 0
                job.status = "completed"
                job.progress = 100
                job.completed_at = datetime.utcnow()
                job.result_data = {"files_scanned": 0}
                await session.commit()
                return

            llm = get_provider()
            llm_available = await llm.health_check()
            if not llm_available:
                logger.warning("LLM unavailable, skipping summaries")

            # Delete existing files for this repo (re-scan)
            existing = await session.execute(
                select(CodeFile).where(CodeFile.repository_id == repo_id)
            )
            for f in existing.scalars().all():
                await session.delete(f)
            await session.commit()

            scanned = 0
            test_count = 0

            for i, file_path in enumerate(files):
                progress = 10 + int((i / total) * 85)
                job.progress = progress
                await session.commit()

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue

                ext = file_path.suffix.lstrip(".")
                language = LANGUAGE_MAP.get(ext, "Unknown")
                line_count = content.count("\n") + 1
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                is_test = _detect_test(str(file_path))
                rel_path = str(file_path.relative_to(root))

                summary = None
                role = None
                entities = None

                summarizable = (
                    llm_available
                    and language not in ("JSON", "YAML", "Markdown", "Unknown")
                    and line_count > 5
                    and line_count <= 300
                )
                if summarizable:
                    snippet = content[:1000]
                    prompt = SUMMARIZE_FILE_PROMPT.format(
                        file_path=rel_path,
                        language=language,
                        char_count=len(snippet),
                        content=snippet,
                    )
                    try:
                        response = await asyncio.wait_for(
                            llm.complete(prompt, system=SUMMARIZE_FILE_SYSTEM),
                            timeout=30.0,
                        )
                        raw = response.content.strip()
                        if raw and not raw.endswith("}"):
                            raw = raw.rsplit(",", 1)[0] + "}"
                        data = json.loads(raw)
                        summary = data.get("summary")
                        role = data.get("role")
                        entities = data.get("entities") or []
                    except (asyncio.TimeoutError, Exception) as e:
                        logger.warning("Summary failed for %s: %s", rel_path, e)

                code_file = CodeFile(
                    repository_id=repo_id,
                    project_id=project_id,
                    path=rel_path,
                    language=language,
                    content_hash=content_hash,
                    summary=summary,
                    role_detected=role,
                    entities=entities,
                    is_test_file=is_test,
                    line_count=line_count,
                )
                session.add(code_file)
                scanned += 1
                if is_test:
                    test_count += 1

            await session.commit()

            repo.status = "scanned"
            repo.scanned_at = datetime.utcnow()
            repo.file_count = scanned
            repo.test_count = test_count
            job.status = "completed"
            job.progress = 100
            job.completed_at = datetime.utcnow()
            job.result_data = {"files_scanned": scanned, "test_files": test_count}
            await session.commit()

        except Exception as exc:
            logger.exception("scan_repository failed")
            repo.status = "failed"
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            await session.commit()
            raise
