"""Architect / design graph."""

from __future__ import annotations

import json
from typing import Any

from services.agents import prompt_loader
from services.agents.nodes.llm import invoke_json
from services.agents.state import AgentState
from services.agents.tools.files import write_file
from services.common.logging import get_logger

logger = get_logger(__name__)


async def run(state: dict[str, Any]) -> dict[str, Any]:
    s = AgentState.model_validate(state)
    system = prompt_loader.get("architect")
    user = (
        f"Requirements:\n{json.dumps(s.requirements or {}, indent=2)}\n\n"
        f"Codebase context:\n{s.retrieval_chunks[:8]}"
    )
    try:
        data = await invoke_json(system, user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("design_fallback", error=str(exc))
        data = {
            "components": [
                {"name": "api", "role": "FastAPI HTTP layer"},
                {"name": "store", "role": "URL mapping persistence"},
                {"name": "analytics", "role": "click counters"},
            ],
            "data_model": {
                "urls": {
                    "code": "str pk",
                    "target": "str",
                    "created_at": "datetime",
                    "clicks": "int",
                }
            },
            "api_contract": [
                {"method": "POST", "path": "/shorten", "body": {"url": "string"}},
                {"method": "GET", "path": "/{code}", "response": "302 redirect"},
                {"method": "GET", "path": "/stats/{code}", "response": {"clicks": "int"}},
            ],
            "risks": ["Collision on short codes", "Open redirect abuse"],
            "retrieval_citations": s.retrieval_chunks[:3],
        }
    path = write_file(s.run_id, "design.json", json.dumps(data, indent=2))
    return {
        "design": data,
        "structured": data,
        "content": json.dumps(data),
        "artifact": json.dumps(data),
        "artifacts": {**(s.artifacts or {}), "design": path},
        # Mark plan nodes ready for master DAG
        "implementation_plan": {"status": "ready"},
        "test_plan": {"status": "ready"},
    }
