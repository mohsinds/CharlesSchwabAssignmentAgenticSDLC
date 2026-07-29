"""Judge Temporal activity — layered validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from temporalio import activity

from services.common.config import get_settings
from services.judge.deterministic import run_pytest, validate_code_artifact
from services.judge.llm_judge import judge_artifact
from services.judge.ragas_eval import evaluate_rag
from services.judge.scoring import composite_score


@activity.defn(name="run_judge")
async def run_judge(
    stage_id: str,
    gate: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    settings = get_settings()
    artifacts_dir = Path(settings.artifacts_dir) / context.get("run_id", "unknown")
    code_root = artifacts_dir / "url_shortener"

    deterministic = None
    ragas = None
    llm = None

    if gate in {"ast_parse", "ruff", "bandit", "judge_code"}:
        if code_root.exists():
            deterministic = validate_code_artifact(code_root, settings.coverage_min)
        else:
            content = context.get("code") or context.get("content") or ""
            deterministic = validate_code_artifact(content, settings.coverage_min)

    if gate in {"pytest_run", "coverage_min"}:
        if code_root.exists():
            deterministic = run_pytest(code_root, settings.coverage_min)
        else:
            from services.judge.deterministic import DeterministicResult

            deterministic = DeterministicResult(
                ok=False,
                checks={"pytest_ok": False, "coverage": 0.0},
                findings=["artifact path missing"],
            )

    if gate in {"judge_requirement", "judge_design", "judge_code"}:
        artifact = str(context.get("artifact") or context.get("content") or "")
        criteria = {
            "judge_requirement": "Clear functional/NFR requirements, acceptance criteria, no code.",
            "judge_design": "Components, data model, API contract; cites retrieval for brownfield.",
            "judge_code": "Production-quality, tested, maintainable Python.",
        }.get(gate, "Engineering quality")
        llm = await judge_artifact(
            stage_id,
            artifact,
            criteria,
            deterministic_failed=bool(deterministic and not deterministic.ok),
        )

    if gate == "structural_validation":
        structured = context.get("structured") or {}
        ok = "classification" in structured or "verdict" in structured
        from services.judge.deterministic import DeterministicResult

        deterministic = DeterministicResult(
            ok=ok,
            checks={"structural_ok": ok},
            findings=[] if ok else ["missing classification"],
        )

    if context.get("rag_question") and context.get("rag_answer"):
        ragas = evaluate_rag(
            context["rag_question"],
            context["rag_answer"],
            context.get("rag_contexts") or [],
        )

    score = composite_score(
        deterministic=deterministic,
        ragas=ragas,
        llm=llm,
        gate_name=gate,
    )
    return {
        "passed": score.passed,
        "score": score.score,
        "deterministic_ok": score.deterministic_ok,
        "findings": score.findings,
        "details": score.details,
        "checks": (deterministic.checks if deterministic else {}),
    }
