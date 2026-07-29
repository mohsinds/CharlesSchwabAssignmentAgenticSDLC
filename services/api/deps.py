"""FastAPI dependencies."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from temporalio.client import Client

from services.common.config import get_settings

_temporal: Client | None = None
# In-memory pipeline registry for status when Temporal query unavailable
PIPELINE_REGISTRY: dict[str, dict[str, Any]] = {}


async def get_temporal_client() -> Client | None:
    global _temporal
    settings = get_settings()
    if _temporal is not None:
        return _temporal
    try:
        _temporal = await Client.connect(
            settings.temporal_host,
            namespace=settings.temporal_namespace,
        )
        return _temporal
    except Exception:
        return None


@lru_cache
def settings():
    return get_settings()
