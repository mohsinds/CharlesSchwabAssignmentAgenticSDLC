"""Canonical audit event schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventType(str, Enum):
    ACTIVITY_STARTED = "ActivityStarted"
    ACTIVITY_SUCCEEDED = "ActivitySucceeded"
    ACTIVITY_FAILED = "ActivityFailed"
    GATE_RESULT = "GateResult"
    POLICY_CHECK = "PolicyCheckEvent"
    HITL_DECISION = "HITLDecision"
    REPLAN = "Replan"
    COMPENSATION = "Compensation"
    METRIC_SAMPLE = "MetricSample"
    STAGE_STARTED = "StageStarted"
    STAGE_COMPLETED = "StageCompleted"
    PIPELINE_STARTED = "PipelineStarted"
    PIPELINE_COMPLETED = "PipelineCompleted"


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=_utcnow)
    run_id: str
    workflow_id: str | None = None
    parent_workflow_id: str | None = None
    trace_id: str | None = None
    stage_id: str | None = None
    activity_name: str | None = None
    status: str | None = None
    message: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    elapsed_ms: float | None = None
    redacted: bool = False

    def object_key(self) -> str:
        ts = self.timestamp.strftime("%Y%m%dT%H%M%S%f")
        stage = self.stage_id or "pipeline"
        return f"{self.run_id}/{stage}/{ts}_{self.event_type.value}_{self.event_id}.json"


class PolicyCheckEvent(AuditEvent):
    event_type: EventType = EventType.POLICY_CHECK


class GateResultEvent(AuditEvent):
    event_type: EventType = EventType.GATE_RESULT
