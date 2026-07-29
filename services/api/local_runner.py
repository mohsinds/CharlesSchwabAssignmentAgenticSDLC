"""In-process pipeline runner used when Temporal is unavailable (local demo)."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import uuid4

from services.api.deps import PIPELINE_REGISTRY
from services.audit.event_schema import AuditEvent, EventType
from services.audit.writer import get_audit_writer
from services.common.metrics import PIPELINE_COMPLETED, PIPELINE_STARTED
from services.orchestrator.dag_loader import load_dag


async def run_local_pipeline(
    run_id: str,
    prompt: str,
    mode: str = "live",
    scenario_type: str | None = None,
) -> None:
    writer = get_audit_writer()
    dag = load_dag()
    workflow_id = f"local-{run_id}"
    context: dict[str, Any] = {
        "prompt": prompt,
        "run_id": run_id,
        "mode": mode,
        "scenario_type": scenario_type,
        "artifacts": {},
    }
    PIPELINE_REGISTRY[run_id]["status"] = "running"
    PIPELINE_STARTED.labels(scenario_type=scenario_type or "unknown", mode=mode).inc()

    writer.write(
        AuditEvent(
            event_type=EventType.PIPELINE_STARTED,
            run_id=run_id,
            workflow_id=workflow_id,
            status="started",
            payload={"mode": mode, "local": True},
        )
    )

    if mode == "replay":
        await _replay(run_id, workflow_id, scenario_type or "greenfield")
        PIPELINE_REGISTRY[run_id]["status"] = "completed"
        PIPELINE_COMPLETED.labels(scenario_type=scenario_type or "unknown", status="completed").inc()
        return

    queue = [dag.entry_stage().id]
    completed: set[str] = set()
    terminal = "completed"

    while queue:
        stage_id = queue.pop(0)
        if stage_id in completed:
            continue
        stage = dag.get(stage_id)
        if stage.depends_on and not all(d in completed for d in stage.depends_on):
            queue.append(stage_id)
            await asyncio.sleep(0.01)
            continue

        PIPELINE_REGISTRY[run_id]["current_stage"] = stage_id
        PIPELINE_REGISTRY[run_id]["stage_status"][stage_id] = "running"
        writer.write(
            AuditEvent(
                event_type=EventType.STAGE_STARTED,
                run_id=run_id,
                workflow_id=workflow_id,
                stage_id=stage_id,
                status="started",
            )
        )

        # HITL pause
        if stage.requires_hitl:
            PIPELINE_REGISTRY[run_id]["stage_status"][stage_id] = "waiting_hitl"
            PIPELINE_REGISTRY[run_id]["status"] = "waiting_hitl"
            writer.write(
                AuditEvent(
                    event_type=EventType.HITL_DECISION,
                    run_id=run_id,
                    stage_id=stage_id,
                    status="waiting",
                )
            )
            # Wait until signal updates registry
            for _ in range(3600):
                approvals = PIPELINE_REGISTRY[run_id].setdefault("approvals", {})
                if stage_id in approvals:
                    break
                if PIPELINE_REGISTRY[run_id].get("safe_stop"):
                    terminal = "safe_stop"
                    break
                await asyncio.sleep(0.5)
            else:
                terminal = "rejected"
                break
            if PIPELINE_REGISTRY[run_id].get("safe_stop"):
                break
            notes = approvals.get(stage_id, {}).get("notes")
            if notes:
                context["clarification"] = notes
                context["prompt"] = f"{prompt}\n\nClarification: {notes}"
            context["hitl_approved"] = True
            PIPELINE_REGISTRY[run_id]["status"] = "running"

        try:
            result_key = await _execute_stage(stage, context)
        except Exception as exc:  # noqa: BLE001
            PIPELINE_REGISTRY[run_id]["stage_status"][stage_id] = "failed"
            writer.write(
                AuditEvent(
                    event_type=EventType.ACTIVITY_FAILED,
                    run_id=run_id,
                    stage_id=stage_id,
                    status="failed",
                    message=str(exc),
                )
            )
            terminal = "failed"
            break

        PIPELINE_REGISTRY[run_id]["stage_status"][stage_id] = "completed"
        PIPELINE_REGISTRY[run_id]["artifacts"] = context.get("artifacts") or {}
        writer.write(
            AuditEvent(
                event_type=EventType.STAGE_COMPLETED,
                run_id=run_id,
                workflow_id=workflow_id,
                stage_id=stage_id,
                status="completed",
                payload={"result_key": result_key},
            )
        )
        completed.add(stage_id)
        if stage.terminal:
            break
        for nxt in dag.successors(stage_id, result_key):
            if nxt not in completed and nxt not in queue:
                queue.append(nxt)
        if stage_id in {"implementation_plan", "test_plan"}:
            for cand in ("implementation", "test"):
                if cand in dag.stages and cand not in completed and cand not in queue:
                    queue.append(cand)

    PIPELINE_REGISTRY[run_id]["status"] = terminal
    PIPELINE_REGISTRY[run_id]["current_stage"] = None
    writer.write(
        AuditEvent(
            event_type=EventType.PIPELINE_COMPLETED,
            run_id=run_id,
            workflow_id=workflow_id,
            status=terminal,
            payload={"stages": PIPELINE_REGISTRY[run_id]["stage_status"]},
        )
    )
    PIPELINE_COMPLETED.labels(scenario_type=scenario_type or "unknown", status=terminal).inc()


async def _execute_stage(stage, context: dict[str, Any]) -> str | None:
    from services.orchestrator.activities.agent_activity import run_agent
    from services.orchestrator.activities.retrieval_activity import ingest_codebase, noop_plan

    if stage.activity == "ingest_codebase":
        result = await ingest_codebase(context["run_id"], context.get("seed_path"))
        context.update(result)
        return None
    if stage.activity == "noop_plan":
        result = await noop_plan(context["run_id"], stage.id, context)
        context[stage.id] = result
        return None
    if stage.agent:
        state = {
            "run_id": context["run_id"],
            "trace_id": context["run_id"],
            "stage_id": stage.id,
            "prompt": context.get("prompt", ""),
            "mode": context.get("mode", "live"),
            "scenario_type": context.get("scenario_type"),
            "artifacts": context.get("artifacts") or {},
            "design": context.get("design"),
            "requirements": context.get("requirements"),
            "classification": context.get("classification"),
            "clarification": context.get("clarification"),
            "retrieval_chunks": context.get("chunks") or [],
        }
        result = await run_agent(stage.agent, state)
        context.update(result)
        if stage.on_result:
            classification = result.get("classification") or (result.get("structured") or {}).get(
                "classification"
            )
            if classification in stage.on_result:
                return classification
        return None
    return None


async def _replay(run_id: str, workflow_id: str, scenario: str) -> None:
    from services.orchestrator.activities.replay_artifacts import materialize_replay_artifacts_sync

    writer = get_audit_writer()
    stages = [
        "classify",
        "requirement",
        "design",
        "implementation_plan",
        "test_plan",
        "implementation",
        "test",
        "documentation",
        "release_review",
    ]
    if scenario == "brownfield":
        stages = [
            "classify",
            "codebase_ingest",
            "requirement",
            "design",
            "implementation_plan",
            "test_plan",
            "implementation",
            "test",
            "documentation",
            "release_review",
        ]
    if scenario == "ambiguous":
        stages = [
            "classify",
            "clarify",
            "requirement",
            "design",
            "implementation_plan",
            "test_plan",
            "implementation",
            "test",
            "documentation",
            "release_review",
        ]
    for stage_id in stages:
        PIPELINE_REGISTRY[run_id]["current_stage"] = stage_id
        PIPELINE_REGISTRY[run_id]["stage_status"][stage_id] = "running"
        writer.write(
            AuditEvent(
                event_type=EventType.STAGE_STARTED,
                run_id=run_id,
                workflow_id=workflow_id,
                stage_id=stage_id,
                status="started",
                payload={"mode": "replay"},
            )
        )
        if stage_id in {"clarify", "release_review"}:
            PIPELINE_REGISTRY[run_id]["stage_status"][stage_id] = "waiting_hitl"
            PIPELINE_REGISTRY[run_id]["status"] = "waiting_hitl"
            for _ in range(10):
                if stage_id in PIPELINE_REGISTRY[run_id].setdefault("approvals", {}):
                    break
                await asyncio.sleep(0.2)
            PIPELINE_REGISTRY[run_id].setdefault("approvals", {}).setdefault(
                stage_id, {"notes": "replay-auto"}
            )
            PIPELINE_REGISTRY[run_id]["status"] = "running"
        if stage_id == "implementation":
            materialized = materialize_replay_artifacts_sync(run_id, scenario)
            PIPELINE_REGISTRY[run_id]["artifacts"] = {
                **(materialized.get("artifacts") or {}),
                "files": materialized.get("files") or [],
            }
        await asyncio.sleep(0.15)
        PIPELINE_REGISTRY[run_id]["stage_status"][stage_id] = "completed"
        writer.write(
            AuditEvent(
                event_type=EventType.STAGE_COMPLETED,
                run_id=run_id,
                workflow_id=workflow_id,
                stage_id=stage_id,
                status="completed",
                payload={"mode": "replay"},
            )
        )
    writer.write(
        AuditEvent(
            event_type=EventType.PIPELINE_COMPLETED,
            run_id=run_id,
            workflow_id=workflow_id,
            status="completed",
            payload={
                "mode": "replay",
                "artifacts": PIPELINE_REGISTRY[run_id].get("artifacts") or {},
            },
        )
    )
