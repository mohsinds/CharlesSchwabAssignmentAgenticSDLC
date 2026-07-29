"""Audit-emitting Temporal activities."""

from __future__ import annotations

from typing import Any

from temporalio import activity

from services.audit.event_schema import AuditEvent, EventType
from services.audit.writer import get_audit_writer


@activity.defn(name="emit_audit_event")
async def emit_audit_event(event_dict: dict[str, Any]) -> dict[str, Any]:
    event = AuditEvent.model_validate(event_dict)
    return get_audit_writer().write(event)


def make_event(
    event_type: EventType,
    run_id: str,
    **kwargs: Any,
) -> dict[str, Any]:
    return AuditEvent(event_type=event_type, run_id=run_id, **kwargs).model_dump(mode="json")
