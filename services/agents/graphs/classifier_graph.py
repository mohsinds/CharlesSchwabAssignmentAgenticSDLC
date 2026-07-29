"""Classifier + clarifier graphs."""

from __future__ import annotations

from typing import Any

from services.agents import prompt_loader
from services.agents.nodes.llm import classify_heuristic, invoke_json
from services.agents.state import AgentState
from services.common.logging import get_logger

logger = get_logger(__name__)


async def run(state: dict[str, Any]) -> dict[str, Any]:
    s = AgentState.model_validate(state)
    system = prompt_loader.get("classifier")
    try:
        data = await invoke_json(system, s.prompt)
        classification = data.get("classification") or data.get("verdict")
        if classification not in {"greenfield", "brownfield", "ambiguous"}:
            raise ValueError(f"bad classification: {classification}")
    except Exception as exc:  # noqa: BLE001
        logger.warning("classifier_fallback", error=str(exc))
        data = classify_heuristic(s.prompt)
        classification = data["classification"]

    structured = {
        "classification": classification,
        "verdict": classification,
        "confidence": float(data.get("confidence", 0.5)),
        "rationale": data.get("rationale", ""),
        "questions": data.get("questions") or [],
    }
    return {
        "classification": classification,
        "confidence": structured["confidence"],
        "rationale": structured["rationale"],
        "questions": structured["questions"],
        "structured": structured,
        "scenario_type": classification,
    }


async def run_clarifier(state: dict[str, Any]) -> dict[str, Any]:
    s = AgentState.model_validate(state)
    system = prompt_loader.get("clarifier")
    user = (
        f"Original prompt:\n{s.prompt}\n\n"
        f"Human clarification:\n{s.clarification or '(pending)'}\n\n"
        "Produce refined_requirement JSON with keys: "
        "summary, functional, non_functional, acceptance_criteria, assumptions"
    )
    try:
        data = await invoke_json(system, user)
    except Exception:
        data = {
            "summary": s.clarification or s.prompt,
            "functional": ["URL shorten", "Redirect", "Basic analytics"],
            "non_functional": ["Availability", "Audit logging"],
            "acceptance_criteria": ["API documented", "Tests pass"],
            "assumptions": ["Single-region deployment"],
        }
    return {
        "requirements": data,
        "prompt": data.get("summary") or s.prompt,
        "structured": data,
        "classification": "greenfield",
    }
