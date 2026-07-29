"""Compensation / saga helpers for Temporal workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from services.orchestrator.activities.agent_activity import revert_files
    from services.orchestrator.activities.audit_activity import emit_audit_event, make_event
    from services.audit.event_schema import EventType


@dataclass
class CompensationEntry:
    stage_id: str
    name: str
    args: dict[str, Any] = field(default_factory=dict)


class CompensationStack:
    def __init__(self) -> None:
        self._stack: list[CompensationEntry] = []

    def push(self, entry: CompensationEntry) -> None:
        self._stack.append(entry)

    def items_reversed(self) -> list[CompensationEntry]:
        return list(reversed(self._stack))


async def run_compensations(
    stack: CompensationStack,
    run_id: str,
    workflow_id: str,
) -> list[dict[str, Any]]:
    results = []
    for entry in stack.items_reversed():
        if entry.name == "revert_files":
            result = await workflow.execute_activity(
                revert_files,
                args=[run_id, entry.args.get("snapshot_paths")],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
        else:
            result = {"skipped": True, "name": entry.name}
        await workflow.execute_activity(
            emit_audit_event,
            make_event(
                EventType.COMPENSATION,
                run_id,
                workflow_id=workflow_id,
                stage_id=entry.stage_id,
                activity_name=entry.name,
                status="completed",
                payload=result,
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )
        results.append(result)
    return results
