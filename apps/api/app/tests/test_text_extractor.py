import re

from app.parsers.text_extractor import chunk_text


def test_chunk_text_respects_size_limit_within_oversized_paragraph():
    # Simulates a PDF page extracted as a single huge paragraph (no "\n\n"
    # between requirements) — this used to produce one oversized chunk that
    # got silently truncated downstream.
    lines = [f"REQ-{i:03d}: some requirement text describing feature {i}." for i in range(60)]
    text = "\n".join(lines)

    chunks = chunk_text(text, chunk_size=250)

    assert len(chunks) > 1
    for c in chunks:
        assert len(c["content"]) <= 250 * 4


def test_chunk_text_does_not_drop_any_requirement_id():
    lines = [f"REQ-{i:03d}: some requirement text describing feature {i}." for i in range(60)]
    text = "\n".join(lines)

    chunks = chunk_text(text, chunk_size=250)

    found = set()
    for c in chunks:
        found.update(re.findall(r"REQ-\d+", c["content"]))

    expected = {f"REQ-{i:03d}" for i in range(60)}
    assert found == expected
