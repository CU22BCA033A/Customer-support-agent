import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.kb import router as kb_router
from app.config import get_settings
from app.db import init_db
from app.rag.ingest import run as run_ingest

logger = logging.getLogger("startup")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Rebuild the vector index from knowledge_base/*.md on every boot. This is
    # what makes "drop in a new doc, restart, ask about it" work, and it's also
    # what makes the vector store self-healing on hosts with no persistent disk
    # (e.g. Render's free tier) -- the index is derived entirely from files
    # already in the repo, so there's nothing to lose between deploys.
    try:
        run_ingest()
    except FileNotFoundError as e:
        logger.warning("Skipping startup ingestion: %s", e)
    yield


app = FastAPI(title="AI Customer Support Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(chat_router)
app.include_router(kb_router)
