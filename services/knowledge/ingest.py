"""Ingest codebase directories into the knowledge store."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from services.knowledge.embeddings import embed_texts
from services.knowledge.models import MEMORY_STORE, Chunk
from services.common.logging import get_logger

logger = get_logger(__name__)

TEXT_EXTS = {".py", ".md", ".txt", ".yml", ".yaml", ".toml", ".json"}


def _chunk_text(text: str, size: int = 800) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


async def ingest_directory(path: str, collection: str = "default") -> dict[str, Any]:
    root = Path(path)
    if not root.exists():
        return {"ingested": 0, "collection": collection, "error": f"missing {path}"}

    chunks: list[Chunk] = []
    texts: list[str] = []
    meta: list[tuple[str, str]] = []
    for file in root.rglob("*"):
        if not file.is_file() or file.suffix.lower() not in TEXT_EXTS:
            continue
        try:
            content = file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for part in _chunk_text(content):
            texts.append(part)
            meta.append((str(file.relative_to(root)), part))

    embeddings = await embed_texts(texts) if texts else []
    for (rel, part), emb in zip(meta, embeddings, strict=False):
        chunks.append(
            Chunk(
                id=str(uuid4()),
                collection=collection,
                path=rel,
                text=part,
                embedding=emb,
                metadata={"path": rel},
            )
        )

    MEMORY_STORE[collection] = chunks
    logger.info("ingest_complete", collection=collection, chunks=len(chunks))
    return {"ingested": len(chunks), "collection": collection, "paths": list({c.path for c in chunks})}
