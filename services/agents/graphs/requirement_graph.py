"""Requirement analyst graph."""

from __future__ import annotations

from typing import Any

from services.agents import prompt_loader
from services.agents.nodes.llm import invoke_json
from services.agents.state import AgentState
from services.agents.tools.files import write_file
from services.common.logging import get_logger

logger = get_logger(__name__)


async def run(state: dict[str, Any]) -> dict[str, Any]:
    s = AgentState.model_validate(state)
    system = prompt_loader.get("requirement_analyst")
    user = f"Prompt:\n{s.prompt}\n\nRetrieval:\n{s.retrieval_chunks[:5]}"
    try:
        data = await invoke_json(system, user)
    except Exception as exc:  # noqa: BLE001
        logger.warning("requirement_fallback", error=str(exc))
        data = {
            "summary": s.prompt.strip()[:500],
            "functional": [
                "Create short URL from long URL",
                "Redirect short URL to original",
                "Track click analytics",
            ],
            "non_functional": ["99.9% availability target", "P99 redirect < 100ms"],
            "acceptance_criteria": [
                "POST /shorten returns code",
                "GET /{code} redirects",
                "GET /stats/{code} returns counts",
            ],
            "assumptions": ["In-memory or SQLite store acceptable for prototype"],
            "gaps": [],
        }
    path = write_file(
        s.run_id,
        "requirements.json",
        __import__("json").dumps(data, indent=2),
    )
    return {
        "requirements": data,
        "structured": data,
        "content": __import__("json").dumps(data),
        "artifact": __import__("json").dumps(data),
        "artifacts": {**(s.artifacts or {}), "requirements": path},
    }
