"""API schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PipelineCreate(BaseModel):
    prompt: str = Field(min_length=1)
    scenario_type: Literal["greenfield", "brownfield", "ambiguous"] | None = None
    mode: Literal["live", "replay"] = "live"


class PipelineStatus(BaseModel):
    run_id: str
    workflow_id: str
    status: str
    current_stage: str | None = None
    stage_status: dict[str, str] = Field(default_factory=dict)
    scenario_type: str | None = None
    mode: str = "live"
    artifacts: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None


class SignalRequest(BaseModel):
    action: Literal["approve", "reject", "replan", "safe_stop"]
    stage_id: str | None = None
    reason: str | None = None
    notes: str | None = None
    from_stage: str | None = None
    hint: str | None = None
