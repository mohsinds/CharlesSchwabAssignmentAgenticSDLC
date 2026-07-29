"""In-memory + optional pgvector store models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    id: str
    collection: str
    path: str
    text: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


# Process-local fallback store when Postgres is unavailable
MEMORY_STORE: dict[str, list[Chunk]] = {}
