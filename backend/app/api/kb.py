from pathlib import Path

from fastapi import APIRouter

from app.config import get_settings
from app.rag.vectorstore import get_vector_store

router = APIRouter()


@router.get("/kb/docs")
def list_docs() -> dict:
    settings = get_settings()
    kb_dir = Path(settings.knowledge_base_dir)
    files = sorted(p.name for p in kb_dir.iterdir()) if kb_dir.exists() else []
    return {"documents": files, "chunk_count": get_vector_store().document_count()}
