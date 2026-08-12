#!/usr/bin/env python3
"""CLI entrypoint: (re)build the vector index from backend/knowledge_base/.

Usage:
    python scripts/ingest.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag.ingest import run  # noqa: E402

if __name__ == "__main__":
    run()
