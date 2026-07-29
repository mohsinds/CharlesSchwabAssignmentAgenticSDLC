"""Shared LLM invoke helper with offline heuristics."""

from __future__ import annotations

import json
import re
from typing import Any

from services.common.logging import get_logger

logger = get_logger(__name__)


async def invoke_json(system: str, user: str, *, model: str | None = None) -> dict[str, Any]:
    try:
        from services.common.config import get_chat_model

        llm = get_chat_model(model)
        msg = await llm.ainvoke(
            [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": user + "\n\nRespond with a single JSON object only.",
                },
            ]
        )
        text = msg.content if hasattr(msg, "content") else str(msg)
        return parse_json(text)
    except Exception as exc:  # noqa: BLE001
        logger.warning("llm_invoke_failed", error=str(exc))
        raise


def parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence:
            return json.loads(fence.group(1))
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def classify_heuristic(prompt: str) -> dict[str, Any]:
    p = prompt.lower()
    questions = []
    if any(w in p for w in ("enterprise-ready", "somehow", "improve", "better", "make it")) and not any(
        w in p for w in ("add rate", "add redis", "endpoint", "api for")
    ):
        if "enterprise" in p or "ready" in p or len(p.split()) < 12:
            return {
                "classification": "ambiguous",
                "confidence": 0.7,
                "rationale": "Requirement lacks concrete scope and acceptance criteria.",
                "questions": [
                    "Which compliance controls are in scope (auth, audit, encryption)?",
                    "What SLAs (availability, latency, RPS) must be met?",
                    "Is this greenfield or a change to an existing shortener?",
                ],
            }
    if any(w in p for w in ("existing", "refactor", "add rate", "redis", "brownfield", "enhance")):
        return {
            "classification": "brownfield",
            "confidence": 0.85,
            "rationale": "Change request against an existing codebase.",
            "questions": [],
        }
    return {
        "classification": "greenfield",
        "confidence": 0.8,
        "rationale": "New system/feature request with actionable scope.",
        "questions": questions,
    }
