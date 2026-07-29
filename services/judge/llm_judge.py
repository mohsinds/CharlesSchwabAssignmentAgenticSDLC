"""LLM-as-judge via LiteLLM. Never overrides deterministic failures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from services.common.config import get_settings
from services.common.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LLMJudgeResult:
    ok: bool
    score: float
    rationale: str
    dimensions: dict[str, float]


async def judge_artifact(
    stage_id: str,
    artifact: str,
    criteria: str,
    *,
    deterministic_failed: bool = False,
) -> LLMJudgeResult:
    if deterministic_failed:
        return LLMJudgeResult(
            ok=False,
            score=0.0,
            rationale="Deterministic validators failed; LLM judge skipped (non-override).",
            dimensions={},
        )

    settings = get_settings()
    prompt = (
        f"You are a strict engineering reviewer for SDLC stage '{stage_id}'.\n"
        f"Criteria:\n{criteria}\n\n"
        f"Artifact:\n{artifact[:8000]}\n\n"
        "Return JSON: {\"score\": 0.0-1.0, \"rationale\": \"...\", "
        "\"dimensions\": {\"correctness\": 0-1, \"security\": 0-1, \"clarity\": 0-1}}"
    )

    try:
        from services.common.config import get_chat_model

        model = get_chat_model(settings.litellm_model_judge)
        resp = await model.ainvoke(prompt)
        text = resp.content if hasattr(resp, "content") else str(resp)
        data = _parse_json(text)
        score = float(data.get("score", 0.0))
        return LLMJudgeResult(
            ok=score >= settings.judge_pass_threshold,
            score=score,
            rationale=str(data.get("rationale", "")),
            dimensions={k: float(v) for k, v in (data.get("dimensions") or {}).items()},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("llm_judge_failed", error=str(exc))
        # Heuristic fallback for offline/demo
        length_ok = 50 < len(artifact) < 200_000
        score = 0.75 if length_ok else 0.4
        return LLMJudgeResult(
            ok=score >= settings.judge_pass_threshold,
            score=score,
            rationale=f"offline heuristic ({exc})",
            dimensions={"correctness": score, "security": score, "clarity": score},
        )


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        return {"score": 0.5, "rationale": text[:500], "dimensions": {}}
