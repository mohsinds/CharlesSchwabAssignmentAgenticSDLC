"""Metrics endpoint — Prometheus exposition + JSON summary."""

from __future__ import annotations

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from services.api.deps import PIPELINE_REGISTRY

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics_json() -> dict:
    total = len(PIPELINE_REGISTRY)
    by_status: dict[str, int] = {}
    for rec in PIPELINE_REGISTRY.values():
        by_status[rec.get("status", "unknown")] = by_status.get(rec.get("status", "unknown"), 0) + 1
    return {"pipelines_total": total, "by_status": by_status}


@router.get("/metrics/prometheus")
async def metrics_prometheus() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
