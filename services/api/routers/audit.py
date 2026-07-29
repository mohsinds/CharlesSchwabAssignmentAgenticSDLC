"""Audit routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.api.deps import PIPELINE_REGISTRY
from services.audit.replay import load_run_timeline, summarize_timeline

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/{run_id}")
async def get_audit(run_id: str) -> dict:
    if run_id not in PIPELINE_REGISTRY and not load_run_timeline(run_id):
        raise HTTPException(status_code=404, detail="no audit for run")
    events = load_run_timeline(run_id)
    return {
        "run_id": run_id,
        "summary": summarize_timeline(events),
        "events": [e.model_dump(mode="json") for e in events],
    }
