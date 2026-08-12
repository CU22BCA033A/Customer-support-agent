"""Ingestion pipeline: load knowledge_base/*.md, chunk, embed, and store.

Run directly (`python -m app.rag.ingest`) or via scripts/ingest.py. Safe to
re-run any time a doc is added or edited — chunk ids are stable
(source_file::index) so upsert overwrites in place.
"""

import logging
from pathlib import Path

from app.config import get_settings
from app.rag.chunking import chunk_markdown
from app.rag.vectorstore import get_vector_store

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("ingest")

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt"}


def run(reset: bool = True) -> dict[str, int]:
    settings = get_settings()
    kb_dir = Path(settings.knowledge_base_dir)
    if not kb_dir.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {kb_dir}")

    store = get_vector_store()
    if reset:
        store.reset()

    results: dict[str, int] = {}
    files = sorted(p for p in kb_dir.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    if not files:
        logger.warning("No knowledge base documents found in %s", kb_dir)
        return results

    for path in files:
        text = path.read_text(encoding="utf-8")
        chunks = chunk_markdown(text, fallback_title=path.stem.replace("_", " ").title())
        count = store.add_chunks(source_file=path.name, chunks=chunks)
        results[path.name] = count
        logger.info("  %-30s -> %d chunk(s)", path.name, count)

    total = sum(results.values())
    logger.info("Ingested %d document(s), %d chunk(s) total.", len(results), total)
    return results


if __name__ == "__main__":
    run()
