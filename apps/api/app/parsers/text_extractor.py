import re
from pathlib import Path


def extract_text(file_path: str, file_type: str) -> str:
    match file_type.lower():
        case "pdf":
            return _extract_pdf(file_path)
        case "docx":
            return _extract_docx(file_path)
        case "md" | "markdown" | "txt":
            return Path(file_path).read_text(encoding="utf-8")
        case _:
            raise ValueError(f"Unsupported file type: {file_type}")


def _extract_pdf(file_path: str) -> str:
    import fitz  # PyMuPDF

    doc = fitz.open(file_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages)


def _extract_docx(file_path: str) -> str:
    from docx import Document

    doc = Document(file_path)
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def chunk_text(text: str, chunk_size: int = 500) -> list[dict]:
    """Split text into chunks by section headers or token count (~4 chars/token)."""
    chunks = []
    sections = _split_by_headers(text)

    if len(sections) > 1:
        for title, content in sections:
            if not content.strip():
                continue
            sub_chunks = _split_by_size(content, chunk_size)
            for i, chunk in enumerate(sub_chunks):
                chunks.append({
                    "content": chunk,
                    "section_title": title if i == 0 else f"{title} (suite)",
                })
    else:
        for chunk in _split_by_size(text, chunk_size):
            chunks.append({"content": chunk, "section_title": None})

    return chunks


def _split_by_headers(text: str) -> list[tuple[str, str]]:
    header_pattern = re.compile(r"^(#{1,3}\s+.+)$", re.MULTILINE)
    parts = header_pattern.split(text)

    if len(parts) <= 1:
        return [("", text)]

    sections = []
    current_title = ""
    for i, part in enumerate(parts):
        if header_pattern.match(part.strip()):
            current_title = part.strip().lstrip("#").strip()
        elif part.strip():
            sections.append((current_title, part))

    return sections if sections else [("", text)]


def _split_by_size(text: str, chunk_size: int) -> list[str]:
    char_limit = chunk_size * 4
    if len(text) <= char_limit:
        return [text.strip()]

    chunks = []
    paragraphs = text.split("\n\n")
    current = []
    current_len = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current_len + len(para) > char_limit and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        chunks.append("\n\n".join(current))

    return chunks
