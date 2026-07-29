"""Composite scoring → gate pass/fail."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.common.config import get_settings
from services.judge.deterministic import DeterministicResult
from services.judge.llm_judge import LLMJudgeResult
from services.judge.ragas_eval import RagasResult


@dataclass
class GateScore:
    passed: bool
    score: float
    deterministic_ok: bool
    findings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def composite_score(
    *,
    deterministic: DeterministicResult | None = None,
    ragas: RagasResult | None = None,
    llm: LLMJudgeResult | None = None,
    gate_name: str = "judge",
) -> GateScore:
    settings = get_settings()
    findings: list[str] = []
    details: dict[str, Any] = {"gate": gate_name}

    det_ok = True
    if deterministic is not None:
        det_ok = deterministic.ok
        findings.extend(deterministic.findings)
        details["deterministic"] = deterministic.checks
        if not det_ok:
            # Never let LLM override
            return GateScore(
                passed=False,
                score=0.0,
                deterministic_ok=False,
                findings=findings,
                details=details,
            )

    scores: list[float] = []
    if ragas is not None:
        avg = sum(ragas.scores.values()) / max(len(ragas.scores), 1)
        scores.append(avg)
        findings.extend(ragas.findings)
        details["ragas"] = ragas.scores
        if not ragas.ok:
            return GateScore(
                passed=False,
                score=avg,
                deterministic_ok=det_ok,
                findings=findings,
                details=details,
            )

    if llm is not None:
        scores.append(llm.score)
        details["llm_judge"] = {
            "score": llm.score,
            "rationale": llm.rationale,
            "dimensions": llm.dimensions,
        }
        if not llm.ok:
            findings.append(llm.rationale)

    final = sum(scores) / len(scores) if scores else (1.0 if det_ok else 0.0)
    passed = det_ok and final >= settings.judge_pass_threshold and not findings
    # If only deterministic and ok with no findings
    if deterministic is not None and ragas is None and llm is None:
        passed = det_ok
        final = 1.0 if det_ok else 0.0
    elif llm is not None:
        passed = det_ok and llm.ok and (ragas.ok if ragas else True)

    return GateScore(
        passed=passed,
        score=final,
        deterministic_ok=det_ok,
        findings=findings,
        details=details,
    )
