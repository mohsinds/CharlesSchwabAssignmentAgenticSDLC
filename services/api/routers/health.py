"""Health checks."""

from __future__ import annotations

from fastapi import APIRouter

from services.api.deps import get_temporal_client
from services.common.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    temporal_ok = False
    try:
        client = await get_temporal_client()
        temporal_ok = client is not None
    except Exception:
        temporal_ok = False
    return {
        "status": "ok",
        "temporal": temporal_ok,
        "litellm_base_url": settings.litellm_base_url,
        "version": "0.1.0",
    }
