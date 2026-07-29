"""Temporal worker — registers workflows and activities."""

from __future__ import annotations

import asyncio
import concurrent.futures

from temporalio.client import Client
from temporalio.worker import Worker

from services.common.config import configure_langsmith, get_settings
from services.common.logging import configure_logging, get_logger
from services.orchestrator.activities.agent_activity import revert_files, run_agent
from services.orchestrator.activities.audit_activity import emit_audit_event
from services.orchestrator.activities.judge_activity import run_judge
from services.orchestrator.activities.policy_activity import run_policy_gate
from services.orchestrator.activities.replay_artifacts import materialize_replay_artifacts
from services.orchestrator.activities.retrieval_activity import (
    ingest_codebase,
    load_replay_events,
    noop_plan,
    retrieve_context,
)
from services.orchestrator.workflows.sdlc_master import SDLCMasterWorkflow
from services.orchestrator.workflows.stage_workflow import StageWorkflow

logger = get_logger(__name__)


async def run_worker() -> None:
    configure_logging()
    settings = get_settings()
    tracing_on = configure_langsmith()
    logger.info("langsmith_tracing", enabled=tracing_on)
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
    )
    # Shared process: one worker on workflow queue also polls activity queues via multiple workers
    activity_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)

    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue_workflows,
        workflows=[SDLCMasterWorkflow, StageWorkflow],
        activities=[
            emit_audit_event,
            run_policy_gate,
            run_judge,
            run_agent,
            revert_files,
            ingest_codebase,
            retrieve_context,
            noop_plan,
            load_replay_events,
            materialize_replay_artifacts,
        ],
        activity_executor=activity_executor,
    )
    logger.info(
        "worker_started",
        task_queue=settings.temporal_task_queue_workflows,
        temporal_host=settings.temporal_host,
    )
    await worker.run()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
