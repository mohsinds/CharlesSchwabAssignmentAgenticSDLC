"""LangGraph agent invocation activity."""

from __future__ import annotations

from typing import Any

from temporalio import activity

from services.common.logging import get_logger

logger = get_logger(__name__)

AGENT_MAP = {
    "classifier": "services.agents.graphs.classifier_graph",
    "clarifier": "services.agents.graphs.classifier_graph",  # clarifier uses shared clarify path
    "requirement_analyst": "services.agents.graphs.requirement_graph",
    "architect": "services.agents.graphs.design_graph",
    "implementer": "services.agents.graphs.implementation_graph",
    "tester": "services.agents.graphs.test_graph",
    "documenter": "services.agents.graphs.doc_graph",
}


@activity.defn(name="run_agent")
async def run_agent(
    agent_name: str,
    state: dict[str, Any],
) -> dict[str, Any]:
    activity.heartbeat(f"starting:{agent_name}")
    # Clarifier is a special mode of classifier / dedicated path
    if agent_name == "clarifier":
        from services.agents.graphs.classifier_graph import run_clarifier

        result = await run_clarifier(state)
    else:
        module_path = AGENT_MAP.get(agent_name)
        if not module_path:
            raise ValueError(f"unknown agent: {agent_name}")
        import importlib

        mod = importlib.import_module(module_path)
        result = await mod.run(state)
    activity.heartbeat(f"done:{agent_name}")
    return result


@activity.defn(name="revert_files")
async def revert_files(run_id: str, snapshot_paths: list[str] | None = None) -> dict[str, Any]:
    """Compensation: remove generated implementation artifacts for the run."""
    from pathlib import Path
    import shutil

    from services.common.config import get_settings

    root = Path(get_settings().artifacts_dir) / run_id / "url_shortener"
    removed = False
    if root.exists():
        shutil.rmtree(root)
        removed = True
    logger.info("compensation_revert_files", run_id=run_id, removed=removed)
    return {"reverted": removed, "path": str(root), "snapshots": snapshot_paths or []}
