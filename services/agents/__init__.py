"""Typed serializable agent state."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    run_id: str
    trace_id: str
    stage_id: str
    parent_workflow_id: str | None = None
    prompt: str = ""
    mode: str = "live"
    scenario_type: str | None = None
    classification: str | None = None
    confidence: float | None = None
    questions: list[str] = Field(default_factory=list)
    clarification: str | None = None
    requirements: dict[str, Any] | None = None
    design: dict[str, Any] | None = None
    retrieval_chunks: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    code: str | None = None
    test_report: dict[str, Any] | None = None
    documentation: str | None = None
    structured: dict[str, Any] | None = None
    replan_count: int = 0
    error: str | None = None
    rationale: str | None = None


class ClassifierOutput(BaseModel):
    classification: str  # greenfield | brownfield | ambiguous
    confidence: float
    rationale: str
    questions: list[str] = Field(default_factory=list)
