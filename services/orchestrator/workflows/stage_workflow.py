"""Generic stage runner: entry gates → work → exit gates → retry/HITL."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from services.audit.event_schema import EventType
    from services.orchestrator.activities.agent_activity import run_agent
    from services.orchestrator.activities.audit_activity import emit_audit_event, make_event
    from services.orchestrator.activities.judge_activity import run_judge
    from services.orchestrator.activities.policy_activity import run_policy_gate
    from services.orchestrator.activities.retrieval_activity import (
        ingest_codebase,
        noop_plan,
    )
    from services.orchestrator.dag_loader import StageDef


POLICY_GATES = {
    "pii_check",
    "policy_check",
    "final_policy_check",
}
JUDGE_GATES = {
    "structural_validation",
    "judge_requirement",
    "judge_design",
    "judge_code",
    "ast_parse",
    "ruff",
    "bandit",
    "pytest_run",
    "coverage_min",
}


@dataclass
class StageInput:
    run_id: str
    workflow_id: str
    trace_id: str
    stage: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)
    mode: str = "live"  # live | replay


@dataclass
class StageOutput:
    stage_id: str
    status: str
    result_key: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    requires_hitl: bool = False
    violations: list[str] = field(default_factory=list)
    compensation: str | None = None


@workflow.defn(name="StageWorkflow")
class StageWorkflow:
    def __init__(self) -> None:
        self._approved: dict[str, bool] = {}
        self._reject_reason: str | None = None
        self._safe_stop = False
        self._clarification: str | None = None

    @workflow.signal
    def approve(self, stage_id: str, notes: str = "") -> None:
        self._approved[stage_id] = True
        if notes:
            self._clarification = notes

    @workflow.signal
    def reject(self, stage_id: str, reason: str) -> None:
        self._approved[stage_id] = False
        self._reject_reason = reason

    @workflow.signal
    def safe_stop(self, reason: str = "") -> None:
        self._safe_stop = True
        self._reject_reason = reason or "safe_stop"

    @workflow.run
    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        inp = StageInput(**payload)
        stage = StageDef.from_dict(inp.stage)
        context = dict(inp.context)
        context.setdefault("run_id", inp.run_id)
        context.setdefault("trace_id", inp.trace_id)

        await workflow.execute_activity(
            emit_audit_event,
            make_event(
                EventType.STAGE_STARTED,
                inp.run_id,
                workflow_id=inp.workflow_id,
                stage_id=stage.id,
                status="started",
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )

        if self._safe_stop:
            return StageOutput(
                stage_id=stage.id, status="safe_stop", context=context
            ).__dict__

        # Entry gates
        entry_ok, entry_violations, needs_hitl = await self._run_gates(
            stage, "entry", stage.entry_gates, context, inp
        )
        if not entry_ok:
            if needs_hitl or stage.requires_hitl:
                await self._wait_hitl(stage, inp)
                if self._reject_reason or self._safe_stop:
                    return StageOutput(
                        stage_id=stage.id,
                        status="rejected",
                        context=context,
                        violations=entry_violations,
                    ).__dict__
            else:
                return StageOutput(
                    stage_id=stage.id,
                    status="gate_failed",
                    context=context,
                    violations=entry_violations,
                ).__dict__

        # HITL before work for clarify / explicit requires_hitl stages that pause first
        if stage.requires_hitl and stage.id == "clarify":
            context["clarifying_questions"] = context.get("clarifying_questions") or context.get(
                "questions", []
            )
            await self._wait_hitl(stage, inp)
            if self._reject_reason or self._safe_stop:
                return StageOutput(
                    stage_id=stage.id, status="rejected", context=context
                ).__dict__
            if self._clarification:
                context["clarification"] = self._clarification
                context["prompt"] = (
                    f"{context.get('prompt', '')}\n\nClarification: {self._clarification}"
                )

        # Execute work with retries
        attempts = 0
        max_attempts = max(stage.retry_max, 0) + 1
        last_error: list[str] = []
        agent_result: dict[str, Any] = {}

        while attempts < max_attempts:
            attempts += 1
            try:
                agent_result = await self._execute_work(stage, context, inp)
                context.update(agent_result.get("context_updates") or {})
                for k, v in agent_result.items():
                    if k != "context_updates":
                        context[k] = v
                break
            except Exception as exc:  # noqa: BLE001 — activity failures surface here
                last_error = [str(exc)]
                if attempts >= max_attempts:
                    return StageOutput(
                        stage_id=stage.id,
                        status="failed",
                        context=context,
                        violations=last_error,
                        compensation=stage.compensation,
                    ).__dict__

        # Exit gates
        exit_ok, exit_violations, needs_hitl = await self._run_gates(
            stage, "exit", stage.exit_gates, context, inp
        )
        if not exit_ok:
            if attempts < max_attempts and stage.retry_max > 0:
                # retry loop already consumed; escalate
                pass
            if needs_hitl or stage.requires_hitl or stage.id == "release_review":
                await self._wait_hitl(stage, inp)
                if stage.id == "release_review" and self._approved.get(stage.id):
                    context["hitl_approved"] = True
                    exit_ok, exit_violations, _ = await self._run_gates(
                        stage, "exit", stage.exit_gates, context, inp
                    )
                elif not self._approved.get(stage.id):
                    return StageOutput(
                        stage_id=stage.id,
                        status="rejected",
                        context=context,
                        violations=exit_violations,
                        compensation=stage.compensation,
                    ).__dict__
            if not exit_ok:
                return StageOutput(
                    stage_id=stage.id,
                    status="gate_failed",
                    context=context,
                    violations=exit_violations,
                    compensation=stage.compensation,
                ).__dict__

        if stage.requires_hitl and stage.id == "release_review" and not self._approved.get(stage.id):
            await self._wait_hitl(stage, inp)
            if not self._approved.get(stage.id):
                return StageOutput(
                    stage_id=stage.id, status="rejected", context=context
                ).__dict__
            context["hitl_approved"] = True

        result_key = None
        if stage.on_result:
            classification = (
                context.get("classification")
                or (context.get("structured") or {}).get("classification")
                or (context.get("structured") or {}).get("verdict")
            )
            if classification in stage.on_result:
                result_key = classification

        await workflow.execute_activity(
            emit_audit_event,
            make_event(
                EventType.STAGE_COMPLETED,
                inp.run_id,
                workflow_id=inp.workflow_id,
                stage_id=stage.id,
                status="completed",
                payload={"result_key": result_key},
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )

        return StageOutput(
            stage_id=stage.id,
            status="completed",
            result_key=result_key,
            context=context,
            compensation=stage.compensation,
        ).__dict__

    async def _wait_hitl(self, stage: StageDef, inp: StageInput) -> None:
        await workflow.execute_activity(
            emit_audit_event,
            make_event(
                EventType.HITL_DECISION,
                inp.run_id,
                workflow_id=inp.workflow_id,
                stage_id=stage.id,
                status="waiting",
                message="awaiting human approval",
            ),
            start_to_close_timeout=timedelta(seconds=30),
        )
        try:
            await workflow.wait_condition(
                lambda: stage.id in self._approved or self._safe_stop,
                timeout=timedelta(seconds=stage.hitl_timeout_seconds),
            )
        except TimeoutError:
            self._reject_reason = "hitl_timeout"
            self._approved[stage.id] = False

    async def _run_gates(
        self,
        stage: StageDef,
        phase: str,
        gates: list[str],
        context: dict[str, Any],
        inp: StageInput,
    ) -> tuple[bool, list[str], bool]:
        violations: list[str] = []
        needs_hitl = False
        for gate in gates:
            if gate in POLICY_GATES or gate == "pii_check":
                payload = {
                    "content": context.get("prompt") or context.get("content") or "",
                    "structured": context.get("structured"),
                    "hitl_approved": context.get("hitl_approved", False),
                    "design_present": bool(context.get("design")),
                    "ast_ok": (context.get("checks") or {}).get("ast_ok", True),
                    "ruff_ok": (context.get("checks") or {}).get("ruff_ok", True),
                    "pytest_ok": (context.get("checks") or {}).get("pytest_ok", True),
                    "coverage": (context.get("checks") or {}).get("coverage"),
                    **{k: context.get(k) for k in ("requires_destructive", "approved")},
                }
                decision = await workflow.execute_activity(
                    run_policy_gate,
                    args=[stage.id, phase, payload, gate],
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=RetryPolicy(maximum_attempts=3),
                )
                await workflow.execute_activity(
                    emit_audit_event,
                    make_event(
                        EventType.GATE_RESULT,
                        inp.run_id,
                        workflow_id=inp.workflow_id,
                        stage_id=stage.id,
                        status="passed" if decision["allowed"] else "failed",
                        payload=decision,
                    ),
                    start_to_close_timeout=timedelta(seconds=30),
                )
                if not decision["allowed"]:
                    violations.extend(decision.get("violations") or [])
                    needs_hitl = needs_hitl or decision.get("requires_hitl", False)
            elif gate in JUDGE_GATES:
                result = await workflow.execute_activity(
                    run_judge,
                    args=[stage.id, gate, context],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )
                context["checks"] = {
                    **(context.get("checks") or {}),
                    **(result.get("checks") or {}),
                }
                await workflow.execute_activity(
                    emit_audit_event,
                    make_event(
                        EventType.GATE_RESULT,
                        inp.run_id,
                        workflow_id=inp.workflow_id,
                        stage_id=stage.id,
                        status="passed" if result["passed"] else "failed",
                        payload=result,
                    ),
                    start_to_close_timeout=timedelta(seconds=30),
                )
                if not result["passed"]:
                    violations.extend(result.get("findings") or ["judge failed"])
            else:
                # Unknown gate → policy check
                decision = await workflow.execute_activity(
                    run_policy_gate,
                    args=[stage.id, phase, {"content": str(context)}, gate],
                    start_to_close_timeout=timedelta(seconds=60),
                )
                if not decision["allowed"]:
                    violations.extend(decision.get("violations") or [])
        return len(violations) == 0, violations, needs_hitl

    async def _execute_work(
        self, stage: StageDef, context: dict[str, Any], inp: StageInput
    ) -> dict[str, Any]:
        if stage.activity == "ingest_codebase":
            return await workflow.execute_activity(
                ingest_codebase,
                args=[inp.run_id, context.get("seed_path")],
                start_to_close_timeout=timedelta(minutes=10),
                heartbeat_timeout=timedelta(seconds=30),
            )
        if stage.activity == "noop_plan":
            return await workflow.execute_activity(
                noop_plan,
                args=[inp.run_id, stage.id, context],
                start_to_close_timeout=timedelta(seconds=30),
            )
        if stage.agent:
            state = {
                "run_id": inp.run_id,
                "trace_id": inp.trace_id,
                "stage_id": stage.id,
                "parent_workflow_id": inp.workflow_id,
                "prompt": context.get("prompt", ""),
                "mode": inp.mode,
                "scenario_type": context.get("scenario_type"),
                "artifacts": context.get("artifacts") or {},
                "design": context.get("design"),
                "requirements": context.get("requirements"),
                "classification": context.get("classification"),
                "clarification": context.get("clarification"),
                "retrieval_chunks": context.get("chunks") or context.get("retrieval_chunks") or [],
            }
            return await workflow.execute_activity(
                run_agent,
                args=[stage.agent, state],
                start_to_close_timeout=timedelta(minutes=15),
                heartbeat_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=2),
            )
        # release_review with no agent — pass through
        return {"status": "ready_for_release"}
