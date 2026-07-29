"""Embedding helpers via LiteLLM with hash fallback."""

from __future__ import annotations

import hashlib
import math
from typing import Sequence


def _hash_embed(text: str, dim: int = 64) -> list[float]:
    vec = [0.0] * dim
    for token in text.lower().split():
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    try:
        from services.common.config import get_embeddings

        emb = get_embeddings()
        return await emb.aembed_documents(list(texts))
    except Exception:
        return [_hash_embed(t) for t in texts]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b, strict=True))
