"""Tester graph."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from services.agents import prompt_loader
from services.agents.nodes.llm import invoke_json
from services.agents.state import AgentState
from services.agents.tools.files import write_file
from services.common.config import get_settings
from services.common.logging import get_logger
from services.judge.deterministic import run_pytest

logger = get_logger(__name__)


async def run(state: dict[str, Any]) -> dict[str, Any]:
    s = AgentState.model_validate(state)
    settings = get_settings()
    root = Path(settings.artifacts_dir) / s.run_id / "url_shortener"
    system = prompt_loader.get("tester")

    if not (root / "test_app.py").exists() and not list(root.glob("test_*.py")):
        try:
            data = await invoke_json(
                system,
                f"Generate pytest file content JSON {{\"test_app.py\": \"...\"}} for:\n{s.code or ''}",
            )
            for name, content in (data if isinstance(data, dict) else {}).items():
                if name.endswith(".py"):
                    write_file(s.run_id, f"url_shortener/{name}", content)
        except Exception as exc:  # noqa: BLE001
            logger.warning("tester_gen_fallback", error=str(exc))

    report = run_pytest(root, settings.coverage_min) if root.exists() else None
    payload = {
        "ok": report.ok if report else False,
        "checks": report.checks if report else {},
        "findings": report.findings if report else ["missing artifact root"],
    }
    path = write_file(s.run_id, "test_report.json", json.dumps(payload, indent=2))
    return {
        "test_report": payload,
        "checks": payload.get("checks") or {},
        "structured": payload,
        "artifacts": {**(s.artifacts or {}), "test_report": path},
        "content": json.dumps(payload),
        "artifact": json.dumps(payload),
    }
