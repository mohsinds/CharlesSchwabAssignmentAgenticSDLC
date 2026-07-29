"""Policy gate Temporal activity."""

from __future__ import annotations

from typing import Any

from temporalio import activity

from services.policy_engine.policy_gate import check as policy_check


@activity.defn(name="run_policy_gate")
async def run_policy_gate(
    stage_id: str,
    phase: str,
    payload: dict[str, Any],
    gate: str | None = None,
) -> dict[str, Any]:
    decision = await policy_check(stage_id, phase, payload, gate=gate)
    return {
        "allowed": decision.allowed,
        "violations": decision.violations,
        "requires_hitl": decision.requires_hitl,
        "redactions": decision.redactions,
        "redacted_content": decision.redacted_content,
        "gate": decision.gate or gate,
        "phase": phase,
        "details": decision.details,
    }
