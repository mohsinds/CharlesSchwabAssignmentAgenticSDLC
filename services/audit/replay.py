"""Rebuild pipeline history from audit events / scenario replay files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.audit.event_schema import AuditEvent, EventType
from services.audit.writer import get_audit_writer
from services.common.config import get_settings


def load_run_timeline(run_id: str) -> list[AuditEvent]:
    return get_audit_writer().list_run(run_id)


def load_replay_file(scenario: str) -> list[dict[str, Any]]:
    settings = get_settings()
    path = settings.scenarios_dir / scenario / "replay.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("events", [])
    return data


def summarize_timeline(events: list[AuditEvent]) -> dict[str, Any]:
    stages: dict[str, str] = {}
    for e in events:
        if e.stage_id and e.event_type in {
            EventType.STAGE_STARTED,
            EventType.STAGE_COMPLETED,
            EventType.GATE_RESULT,
            EventType.ACTIVITY_FAILED,
        }:
            stages[e.stage_id] = e.status or e.event_type.value
    terminal = next(
        (e for e in reversed(events) if e.event_type == EventType.PIPELINE_COMPLETED),
        None,
    )
    return {
        "event_count": len(events),
        "stages": stages,
        "status": terminal.status if terminal else "running",
        "run_id": events[0].run_id if events else None,
    }


def write_replay_template(path: Path, events: list[AuditEvent]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"events": [e.model_dump(mode="json") for e in events]}
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
