from app.rag.chunking import chunk_markdown

SAMPLE = """# Sample Policy

## Section One

Some content about section one that is reasonably short.

## Section Two

More content here, describing section two in a few sentences.
"""


def test_splits_by_heading():
    chunks = chunk_markdown(SAMPLE, fallback_title="fallback")
    assert len(chunks) == 2
    assert chunks[0].doc_title == "Sample Policy"
    assert chunks[0].heading == "Section One"
    assert "section one" in chunks[0].text
    assert chunks[1].heading == "Section Two"


def test_no_headings_falls_back_to_single_chunk():
    chunks = chunk_markdown("Just plain text, no headings at all.", fallback_title="My Doc")
    assert len(chunks) == 1
    assert chunks[0].doc_title == "My Doc"
    assert chunks[0].heading == "My Doc"


def test_empty_document_produces_no_chunks():
    assert chunk_markdown("   \n\n  ", fallback_title="Empty") == []


def test_long_section_is_split_but_keeps_heading():
    long_body = "\n\n".join(f"Paragraph {i} " + "word " * 200 for i in range(6))
    doc = f"# Doc\n\n## Big Section\n\n{long_body}\n"
    chunks = chunk_markdown(doc, fallback_title="fallback")
    assert len(chunks) > 1
    assert all(c.heading == "Big Section" for c in chunks)
    assert all(len(c.text) <= 1800 + 50 for c in chunks)  # small slack for boundary paragraph
