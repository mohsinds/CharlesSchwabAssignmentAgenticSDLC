"""Pipeline routes."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from services.api.deps import PIPELINE_REGISTRY, get_temporal_client
from services.api.local_runner import run_local_pipeline
from services.api.schemas.pipelines import PipelineCreate, PipelineStatus
from services.api.sse import event_generator
from services.common.config import get_settings
from services.orchestrator.dag_loader import load_dag

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("/meta/dag")
async def get_dag_definition() -> dict[str, Any]:
    dag = load_dag()
    return {
        "name": dag.name,
        "version": dag.version,
        "stages": [
            {
                "id": dag.stages[i].id,
                "agent": dag.stages[i].agent,
                "activity": dag.stages[i].activity,
                "next": dag.stages[i].next,
                "on_result": dag.stages[i].on_result,
                "parallel_after": dag.stages[i].parallel_after,
                "depends_on": dag.stages[i].depends_on,
                "requires_hitl": dag.stages[i].requires_hitl,
                "terminal": dag.stages[i].terminal,
            }
            for i in dag.order
            if i in dag.stages
        ],
    }


@router.post("", response_model=PipelineStatus)
async def create_pipeline(body: PipelineCreate, background: BackgroundTasks) -> PipelineStatus:
    run_id = str(uuid4())
    workflow_id = f"sdlc-{run_id}"
    settings = get_settings()

    PIPELINE_REGISTRY[run_id] = {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "status": "starting",
        "current_stage": None,
        "stage_status": {},
        "scenario_type": body.scenario_type,
        "mode": body.mode,
        "artifacts": {},
        "prompt": body.prompt,
        "approvals": {},
    }

    client = await get_temporal_client()
    started_temporal = False
    if client is not None:
        try:
            from services.orchestrator.workflows.sdlc_master import SDLCMasterWorkflow

            await client.start_workflow(
                SDLCMasterWorkflow.run,
                {
                    "run_id": run_id,
                    "prompt": body.prompt,
                    "mode": body.mode,
                    "scenario_type": body.scenario_type,
                    "trace_id": run_id,
                },
                id=workflow_id,
                task_queue=settings.temporal_task_queue_workflows,
            )
            PIPELINE_REGISTRY[run_id]["status"] = "running"
            PIPELINE_REGISTRY[run_id]["backend"] = "temporal"
            started_temporal = True
        except Exception:
            started_temporal = False

    if not started_temporal:
        PIPELINE_REGISTRY[run_id]["backend"] = "local"
        PIPELINE_REGISTRY[run_id]["status"] = "running"
        background.add_task(run_local_pipeline, run_id, body.prompt, body.mode, body.scenario_type)

    return PipelineStatus(
        run_id=run_id,
        workflow_id=workflow_id,
        status=PIPELINE_REGISTRY[run_id]["status"],
        scenario_type=body.scenario_type,
        mode=body.mode,
    )


@router.get("/{run_id}", response_model=PipelineStatus)
async def get_pipeline(run_id: str) -> PipelineStatus:
    rec = PIPELINE_REGISTRY.get(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="pipeline not found")

    if rec.get("backend") == "temporal":
        client = await get_temporal_client()
        if client:
            try:
                handle = client.get_workflow_handle(rec["workflow_id"])
                status = await handle.query("get_status")
                if isinstance(status, dict):
                    rec["status"] = status.get("status", rec["status"])
                    rec["current_stage"] = status.get("current_stage")
                    rec["stage_status"] = status.get("stage_status") or rec["stage_status"]
                    if status.get("artifacts"):
                        rec["artifacts"] = status["artifacts"]
            except Exception:
                pass

    # Always enrich from disk so Temporal/worker-written files are visible.
    artifacts = dict(rec.get("artifacts") or {})
    try:
        from services.agents.tools.files import list_artifacts

        files = list_artifacts(run_id)
        if files:
            artifacts = {**artifacts, "files": files}
            rec["artifacts"] = artifacts
    except Exception:
        pass

    return PipelineStatus(
        run_id=run_id,
        workflow_id=rec["workflow_id"],
        status=rec["status"],
        current_stage=rec.get("current_stage"),
        stage_status=rec.get("stage_status") or {},
        scenario_type=rec.get("scenario_type"),
        mode=rec.get("mode", "live"),
        artifacts=artifacts,
    )


@router.get("/{run_id}/events")
async def stream_events(run_id: str):
    if run_id not in PIPELINE_REGISTRY:
        raise HTTPException(status_code=404, detail="pipeline not found")
    return EventSourceResponse(event_generator(run_id))
