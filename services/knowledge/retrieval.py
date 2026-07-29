"""Retrieve similar chunks for brownfield reasoning."""

from __future__ import annotations

from typing import Any

from services.knowledge.embeddings import cosine, embed_texts
from services.knowledge.models import MEMORY_STORE


async def retrieve(query: str, collection: str = "default", k: int = 5) -> list[str]:
    chunks = MEMORY_STORE.get(collection) or []
    if not chunks:
        # Fall back to any collection
        for v in MEMORY_STORE.values():
            chunks = v
            break
    if not chunks:
        return []
    q_emb = (await embed_texts([query]))[0]
    ranked = sorted(
        chunks,
        key=lambda c: cosine(q_emb, c.embedding),
        reverse=True,
    )
    return [f"[{c.path}]\n{c.text}" for c in ranked[:k]]


async def retrieve_detailed(query: str, collection: str = "default", k: int = 5) -> list[dict[str, Any]]:
    texts = await retrieve(query, collection=collection, k=k)
    return [{"text": t} for t in texts]
