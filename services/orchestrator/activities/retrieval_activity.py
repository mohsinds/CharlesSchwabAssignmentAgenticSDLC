"""Codebase retrieval / ingest activities."""

from __future__ import annotations

from typing import Any

from temporalio import activity

from services.common.config import get_settings


@activity.defn(name="ingest_codebase")
async def ingest_codebase(run_id: str, seed_path: str | None = None) -> dict[str, Any]:
    from services.knowledge.ingest import ingest_directory

    settings = get_settings()
    path = seed_path or str(settings.scenarios_dir / "brownfield" / "seed_repo")
    result = await ingest_directory(path, collection=f"run_{run_id}")
    return result


@activity.defn(name="retrieve_context")
async def retrieve_context(run_id: str, query: str, k: int = 5) -> dict[str, Any]:
    from services.knowledge.retrieval import retrieve

    chunks = await retrieve(query, collection=f"run_{run_id}", k=k)
    return {"chunks": chunks, "query": query}


@activity.defn(name="noop_plan")
async def noop_plan(run_id: str, plan_name: str, context: dict[str, Any]) -> dict[str, Any]:
    """Synthetic plan node after design (implementation_plan / test_plan)."""
    return {
        "plan": plan_name,
        "run_id": run_id,
        "status": "ready",
        "from_design": bool(context.get("design")),
    }


@activity.defn(name="load_replay_events")
async def load_replay_events(scenario: str) -> list[dict[str, Any]]:
    """Read scenarios/<scenario>/replay.json. File I/O must happen in an
    Activity, never in workflow code (determinism boundary)."""
    import json

    settings = get_settings()
    path = settings.scenarios_dir / scenario / "replay.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    events = data.get("events", data) if isinstance(data, dict) else data
    return events or []
