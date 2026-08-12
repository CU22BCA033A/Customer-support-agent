"""Heading-based markdown chunking.

Splits a markdown document along its heading structure (H1/H2) instead of by a
fixed character count, so each chunk is a semantically complete section that a
retriever can cite back to a specific part of a document.
"""

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^(#{1,2})\s+(.*)$", re.MULTILINE)
MAX_CHUNK_CHARS = 1800


@dataclass
class Chunk:
    doc_title: str
    heading: str
    text: str
    chunk_index: int


def chunk_markdown(text: str, fallback_title: str) -> list[Chunk]:
    """Split markdown into (heading, section_text) chunks.

    The first H1 found becomes the document title. Each H2 becomes its own
    chunk, prefixed with the document title so retrieval results stay
    self-describing even out of context. Sections longer than
    MAX_CHUNK_CHARS are further split on paragraph breaks, still tagged with
    the same heading, so a single chunk never spans two unrelated topics or
    grows too large for a useful citation.
    """
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        body = text.strip()
        return [Chunk(fallback_title, fallback_title, body, 0)] if body else []

    doc_title = fallback_title
    first = matches[0]
    if first.group(1) == "#":
        doc_title = first.group(2).strip()

    sections: list[tuple[str, str]] = []  # (heading, body)
    for i, m in enumerate(matches):
        level, heading = m.group(1), m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if level == "#":
            # H1 with no content of its own (just a title line) — skip as a section
            if body:
                sections.append((doc_title, body))
        else:
            sections.append((heading, body))

    chunks: list[Chunk] = []
    idx = 0
    for heading, body in sections:
        if not body:
            continue
        for piece in _split_long_section(body):
            chunks.append(Chunk(doc_title=doc_title, heading=heading, text=piece, chunk_index=idx))
            idx += 1
    return chunks


def _split_long_section(body: str) -> list[str]:
    if len(body) <= MAX_CHUNK_CHARS:
        return [body]

    paragraphs = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    pieces: list[str] = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) > MAX_CHUNK_CHARS and current:
            pieces.append(current.strip())
            current = para
        else:
            current = candidate
    if current.strip():
        pieces.append(current.strip())
    return pieces or [body]
