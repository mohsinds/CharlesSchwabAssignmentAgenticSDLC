"""HITL / control signals."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from services.api.deps import PIPELINE_REGISTRY, get_temporal_client
from services.api.schemas.pipelines import SignalRequest
from services.audit.event_schema import AuditEvent, EventType
from services.audit.writer import get_audit_writer

router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("/{run_id}")
async def send_signal(run_id: str, body: SignalRequest) -> dict:
    rec = PIPELINE_REGISTRY.get(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="pipeline not found")

    writer = get_audit_writer()
    writer.write(
        AuditEvent(
            event_type=EventType.HITL_DECISION,
            run_id=run_id,
            workflow_id=rec.get("workflow_id"),
            stage_id=body.stage_id,
            status=body.action,
            payload=body.model_dump(),
        )
    )

    # Local backend
    if rec.get("backend") == "local":
        if body.action == "approve":
            stage = body.stage_id or rec.get("current_stage") or "release_review"
            rec.setdefault("approvals", {})[stage] = {"notes": body.notes or ""}
        elif body.action == "reject":
            stage = body.stage_id or rec.get("current_stage")
            if stage:
                rec.setdefault("approvals", {})[stage] = {"rejected": True, "reason": body.reason}
            rec["status"] = "rejected"
        elif body.action == "safe_stop":
            rec["safe_stop"] = True
            rec["status"] = "safe_stop"
        elif body.action == "replan":
            rec["replan"] = {"from_stage": body.from_stage, "hint": body.hint}
        return {"ok": True, "backend": "local"}

    client = await get_temporal_client()
    if not client:
        raise HTTPException(status_code=503, detail="temporal unavailable")

    handle = client.get_workflow_handle(rec["workflow_id"])
    if body.action == "approve":
        await handle.signal("approve", args=[body.stage_id or "", body.notes or ""])
        # Also signal child if present
        child_id = f"{rec['workflow_id']}:{body.stage_id}" if body.stage_id else None
        if child_id:
            try:
                child = client.get_workflow_handle(child_id)
                await child.signal("approve", args=[body.stage_id, body.notes or ""])
            except Exception:
                pass
    elif body.action == "reject":
        await handle.signal("reject", args=[body.stage_id or "", body.reason or ""])
    elif body.action == "replan":
        await handle.signal("replan", args=[body.from_stage or "requirement", body.hint or ""])
    elif body.action == "safe_stop":
        await handle.signal("safe_stop", args=[body.reason or ""])
    return {"ok": True, "backend": "temporal"}
