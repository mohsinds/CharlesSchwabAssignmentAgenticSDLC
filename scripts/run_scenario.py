#!/usr/bin/env python3
"""Run a scenario against the local API (or in-process)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=["greenfield", "brownfield", "ambiguous"], required=True)
    parser.add_argument("--mode", choices=["live", "replay"], default="replay")
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()

    prompts = {
        "greenfield": (ROOT / "scenarios/greenfield/requirement.md").read_text(encoding="utf-8"),
        "brownfield": (ROOT / "scenarios/brownfield/change_request.md").read_text(encoding="utf-8"),
        "ambiguous": (ROOT / "scenarios/ambiguous/requirement.md").read_text(encoding="utf-8"),
    }
    prompt = prompts[args.scenario]

    try:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{args.api}/pipelines",
                json={"prompt": prompt, "scenario_type": args.scenario, "mode": args.mode},
            )
            resp.raise_for_status()
            data = resp.json()
            print(f"Started pipeline {data['run_id']} status={data['status']}")
            print(f"UI: http://localhost:5173/pipelines/{data['run_id']}")
            return
    except Exception as exc:
        print(f"API unavailable ({exc}); running in-process local runner…")

    from services.api.deps import PIPELINE_REGISTRY
    from services.api.local_runner import run_local_pipeline
    from uuid import uuid4

    run_id = str(uuid4())
    PIPELINE_REGISTRY[run_id] = {
        "run_id": run_id,
        "workflow_id": f"local-{run_id}",
        "status": "running",
        "current_stage": None,
        "stage_status": {},
        "scenario_type": args.scenario,
        "mode": args.mode,
        "artifacts": {},
        "approvals": {},
    }
    await run_local_pipeline(run_id, prompt, args.mode, args.scenario)
    print(f"Completed in-process run {run_id} status={PIPELINE_REGISTRY[run_id]['status']}")


if __name__ == "__main__":
    asyncio.run(main())
