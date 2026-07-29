"""Master SDLC workflow — interprets dag/sdlc.yaml at runtime."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from services.audit.event_schema import EventType
    from services.orchestrator.activities.audit_activity import emit_audit_event, make_event
    from services.orchestrator.dag_loader import load_dag
    from services.orchestrator.workflows.compensation import (
        CompensationEntry,
        CompensationStack,
        run_compensations,
    )
    from services.orchestrator.activities.replay_artifacts import materialize_replay_artifacts
    from services.orchestrator.activities.retrieval_activity import load_replay_events
    from services.orchestrator.workflows.stage_workflow import StageWorkflow


@workflow.defn(name="SDLCMasterWorkflow")
class SDLCMasterWorkflow:
    def __init__(self) -> None:
        self._replan_from: str | None = None
        self._replan_hint: str = ""
        self._safe_stop = False
        self._status = "running"
        self._current_stage: str | None = None
        self._context: dict[str, Any] = {}
        self._stage_status: dict[str, str] = {}

    @workflow.signal
    def approve(self, stage_id: str, notes: str = "") -> None:
        # Forwarded by API to child; also recorded at master for status
        self._context.setdefault("approvals", {})[stage_id] = {"notes": notes}

    @workflow.signal
    def reject(self, stage_id: str, reason: str) -> None:
        self._context.setdefault("rejections", {})[stage_id] = reason

    @workflow.signal
    def replan(self, from_stage: str, hint: str = "") -> None:
        self._replan_from = from_stage
        self._replan_hint = hint

    @workflow.signal
    def safe_stop(self, reason: str = "") -> None:
        self._safe_stop = True
        self._status = "safe_stop"
        self._context["safe_stop_reason"] = reason

    @workflow.query
    def get_status(self) -> dict[str, Any]:
        return {
            "status": self._status,
            "current_stage": self._current_stage,
            "stage_status": dict(self._stage_status),
            "context_keys": list(self._context.keys()),
            "artifacts": self._context.get("artifacts") or {},
        }

    @workflow.run
    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        run_id = payload["run_id"]
        prompt = payload.get("prompt", "")
        mode = payload.get("mode", "live")
        scenario_type = payload.get("scenario_type")
        trace_id = payload.get("trace_id") or run_id
        workflow_id = workflow.info().workflow_id

        dag = load_dag()
        compensations = CompensationStack()
        context: dict[str, Any] = {
            "prompt": prompt,
            "mode": mode,
            "scenario_type": scenario_type,
            "run_id": run_id,
            "artifacts": {},
        }
        self._context = context

        await workflow.execute_activity(
            emit_audit_event,
            make_event(
                EventType.PIPELINE_STARTED,
                run_id,
                workflow_id=workflow_id,
                trace_id=trace_id,
                status="started",
                payload={"scenario_type": scenario_type, "mode": mode},
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Replay mode: short-circuit with synthetic success path markers
        if mode == "replay":
            return await self._run_replay(run_id, workflow_id, scenario_type or "greenfield", context)

        completed: set[str] = set()
        queue: list[str] = [dag.entry_stage().id]
        terminal_status = "completed"

        try:
            while queue and not self._safe_stop:
                if self._replan_from:
                    target = self._replan_from
                    self._replan_from = None
                    context["replan_hint"] = self._replan_hint
                    await workflow.execute_activity(
                        emit_audit_event,
                        make_event(
                            EventType.REPLAN,
                            run_id,
                            workflow_id=workflow_id,
                            stage_id=target,
                            status="replan",
                            message=self._replan_hint,
                        ),
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                    # Drop downstream completions after replan target
                    queue = [target]
                    continue

                stage_id = queue.pop(0)
                if stage_id in completed:
                    continue
                stage = dag.get(stage_id)

                # Honor depends_on
                if stage.depends_on and not all(d in completed for d in stage.depends_on):
                    queue.append(stage_id)
                    # Avoid tight loop
                    await workflow.sleep(0.1)
                    if all(d in completed or d in queue for d in stage.depends_on):
                        continue
                    continue

                self._current_stage = stage_id
                self._stage_status[stage_id] = "running"

                # Parallel fan-out for parallel_after synthetic nodes
                if stage.parallel_after and stage_id not in {
                    "implementation_plan",
                    "test_plan",
                }:
                    # First run design-like stage itself, then fan-out handled via successors
                    pass

                child_id = f"{workflow_id}:{stage_id}"
                handle = await workflow.start_child_workflow(
                    StageWorkflow.run,
                    {
                        "run_id": run_id,
                        "workflow_id": child_id,
                        "trace_id": trace_id,
                        "stage": {
                            "id": stage.id,
                            "agent": stage.agent,
                            "activity": stage.activity,
                            "entry_gates": stage.entry_gates,
                            "exit_gates": stage.exit_gates,
                            "on_result": stage.on_result,
                            "next": stage.next,
                            "depends_on": stage.depends_on,
                            "parallel_after": stage.parallel_after,
                            "requires_hitl": stage.requires_hitl,
                            "hitl_timeout_seconds": stage.hitl_timeout_seconds,
                            "replan_target": stage.replan_target,
                            "terminal": stage.terminal,
                            "retry": {"max": stage.retry_max, "backoff": stage.retry_backoff},
                            "compensation": stage.compensation,
                        },
                        "context": context,
                        "mode": mode,
                    },
                    id=child_id,
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )
                result = await handle
                status = result.get("status", "failed")
                self._stage_status[stage_id] = status
                context.update(result.get("context") or {})
                self._context = context

                if status in {"failed", "gate_failed", "rejected", "safe_stop"}:
                    if result.get("compensation"):
                        compensations.push(
                            CompensationEntry(
                                stage_id=stage_id,
                                name=result["compensation"],
                            )
                        )
                        await run_compensations(compensations, run_id, workflow_id)
                    terminal_status = status
                    break

                if result.get("compensation"):
                    compensations.push(
                        CompensationEntry(stage_id=stage_id, name=result["compensation"])
                    )

                completed.add(stage_id)
                if stage.terminal:
                    terminal_status = "completed"
                    break

                successors = dag.successors(stage_id, result.get("result_key"))
                # If parallel_after, enqueue all plan nodes then continue to dependents later
                for nxt in successors:
                    if nxt not in completed and nxt not in queue:
                        queue.append(nxt)

                # After both plan nodes complete, implementation/test become runnable via depends_on
                if stage_id in {"implementation_plan", "test_plan"}:
                    for cand in ("implementation", "test"):
                        if cand in dag.stages and cand not in completed and cand not in queue:
                            queue.append(cand)

            if self._safe_stop:
                terminal_status = "safe_stop"
                await run_compensations(compensations, run_id, workflow_id)

        except Exception as exc:  # noqa: BLE001
            terminal_status = "failed"
            context["error"] = str(exc)
            await run_compensations(compensations, run_id, workflow_id)
            raise
        finally:
            self._status = terminal_status
            await workflow.execute_activity(
                emit_audit_event,
                make_event(
                    EventType.PIPELINE_COMPLETED,
                    run_id,
                    workflow_id=workflow_id,
                    trace_id=trace_id,
                    status=terminal_status,
                    payload={"stages": self._stage_status},
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )

        return {
            "run_id": run_id,
            "status": terminal_status,
            "stage_status": self._stage_status,
            "context": {
                k: v
                for k, v in context.items()
                if k
                in {
                    "classification",
                    "requirements",
                    "design",
                    "artifacts",
                    "questions",
                    "clarification",
                    "test_report",
                    "documentation",
                }
            },
        }

    async def _run_replay(
        self,
        run_id: str,
        workflow_id: str,
        scenario: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        # File I/O must happen in an Activity, never directly in workflow code.
        events = await workflow.execute_activity(
            load_replay_events,
            scenario,
            start_to_close_timeout=timedelta(seconds=30),
        )

        stage_order = [
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
            stage_order = [
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
            stage_order = [
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

        for stage_id in stage_order:
            if self._safe_stop:
                break
            self._current_stage = stage_id
            self._stage_status[stage_id] = "running"
            await workflow.execute_activity(
                emit_audit_event,
                make_event(
                    EventType.STAGE_STARTED,
                    run_id,
                    workflow_id=workflow_id,
                    stage_id=stage_id,
                    status="started",
                    payload={"mode": "replay"},
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )
            if stage_id in {"clarify", "release_review"}:
                # Auto-approve in replay after brief wait signal opportunity.
                # wait_condition raises TimeoutError when the deadline elapses
                # without the condition becoming true — that's the expected
                # "no human responded in time" path here, not a failure.
                self._stage_status[stage_id] = "waiting_hitl"
                try:
                    await workflow.wait_condition(
                        lambda s=stage_id: s in self._context.get("approvals", {})
                        or self._safe_stop,
                        timeout=timedelta(seconds=2),
                    )
                except TimeoutError:
                    # asyncio.TimeoutError is an alias of builtins.TimeoutError (py3.11+)
                    pass
                # Auto-approve if no signal (demo convenience)
                self._context.setdefault("approvals", {}).setdefault(stage_id, {"notes": "replay-auto"})

            # Materialize demo code/docs when implementation would have run.
            if stage_id == "implementation":
                materialized = await workflow.execute_activity(
                    materialize_replay_artifacts,
                    args=[run_id, scenario],
                    start_to_close_timeout=timedelta(seconds=30),
                )
                context["artifacts"] = {
                    **(context.get("artifacts") or {}),
                    **(materialized.get("artifacts") or {}),
                    "files": materialized.get("files") or [],
                }
                self._context = context

            await workflow.execute_activity(
                emit_audit_event,
                make_event(
                    EventType.STAGE_COMPLETED,
                    run_id,
                    workflow_id=workflow_id,
                    stage_id=stage_id,
                    status="completed",
                    payload={"mode": "replay"},
                ),
                start_to_close_timeout=timedelta(seconds=30),
            )
            self._stage_status[stage_id] = "completed"
            await workflow.sleep(0.05)

        # Emit any extra replay file events
        for ev in events:
            try:
                ev = dict(ev)
                ev["run_id"] = run_id
                await workflow.execute_activity(
                    emit_audit_event,
                    ev,
                    start_to_close_timeout=timedelta(seconds=30),
                )
            except Exception:
                continue

        self._status = "completed"
        await workflow.execute_activity(
            emit_audit_event,
            make_event(
                EventType.PIPELINE_COMPLETED,
                run_id,
                workflow_id=workflow_id,
                status="completed",
                payload={
                    "mode": "replay",
                    "stages": self._stage_status,
                    "artifacts": context.get("artifacts") or {},
                },
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )
        return {
            "run_id": run_id,
            "status": "completed",
            "stage_status": self._stage_status,
            "context": context,
            "mode": "replay",
        }
