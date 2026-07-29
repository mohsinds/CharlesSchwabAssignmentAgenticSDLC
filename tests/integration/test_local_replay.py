"""Local replay pipeline smoke test."""

from pathlib import Path

import pytest

from services.api.deps import PIPELINE_REGISTRY
from services.api.local_runner import run_local_pipeline
from services.common.config import get_settings


@pytest.mark.asyncio
async def test_replay_greenfield():
    run_id = "test-replay-gf"
    PIPELINE_REGISTRY[run_id] = {
        "run_id": run_id,
        "workflow_id": f"local-{run_id}",
        "status": "running",
        "current_stage": None,
        "stage_status": {},
        "scenario_type": "greenfield",
        "mode": "replay",
        "artifacts": {},
        "approvals": {},
    }
    await run_local_pipeline(run_id, "Build a URL shortener", "replay", "greenfield")
    assert PIPELINE_REGISTRY[run_id]["status"] == "completed"
    assert PIPELINE_REGISTRY[run_id]["stage_status"]["classify"] == "completed"
    assert PIPELINE_REGISTRY[run_id]["stage_status"]["release_review"] == "completed"

    root = Path(get_settings().artifacts_dir) / run_id
    assert (root / "requirements.json").is_file()
    assert (root / "design.json").is_file()
    assert (root / "url_shortener" / "app.py").is_file()
    assert (root / "url_shortener" / "test_app.py").is_file()
    assert (root / "url_shortener" / "README.md").is_file()
    assert (root / "test_report.json").is_file()
    assert PIPELINE_REGISTRY[run_id]["artifacts"].get("files")
