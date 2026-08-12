"""Thin wrapper around the vector database.

Chroma is the local, zero-infra choice for development. All Chroma-specific
calls are confined to this module — swapping in Pinecone or Weaviate later
means rewriting this file, not any of its callers.
"""

from dataclasses import dataclass

import chromadb

from app.config import get_settings
from app.rag.chunking import Chunk

COLLECTION_NAME = "knowledge_base"


@dataclass
class RetrievedChunk:
    doc: str
    heading: str
    text: str
    score: float  # similarity in [0, 1], higher is more relevant


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = chromadb.PersistentClient(path=settings.chroma_dir)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        self._client.delete_collection(COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, source_file: str, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        ids = [f"{source_file}::{c.chunk_index}" for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {"doc": c.doc_title, "heading": c.heading, "source_file": source_file}
            for c in chunks
        ]
        self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(chunks)

    def document_count(self) -> int:
        return self._collection.count()

    def query(self, query_text: str, top_k: int) -> list[RetrievedChunk]:
        if self._collection.count() == 0:
            return []
        result = self._collection.query(
            query_texts=[query_text],
            n_results=min(top_k, self._collection.count()),
        )
        out: list[RetrievedChunk] = []
        docs = result.get("documents") or [[]]
        metas = result.get("metadatas") or [[]]
        dists = result.get("distances") or [[]]
        for text, meta, distance in zip(docs[0], metas[0], dists[0]):
            # Cosine distance = 1 - cosine_similarity, so this recovers similarity in [0, 1].
            similarity = max(0.0, 1.0 - distance)
            out.append(
                RetrievedChunk(
                    doc=meta.get("doc", "Unknown"),
                    heading=meta.get("heading", ""),
                    text=text,
                    score=round(similarity, 4),
                )
            )
        return out


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
