"""Ragas-style RAG quality evaluation with offline heuristic fallback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RagasResult:
    ok: bool
    scores: dict[str, float]
    findings: list[str]


def evaluate_rag(
    question: str,
    answer: str,
    contexts: list[str],
    threshold: float = 0.5,
) -> RagasResult:
    """Score faithfulness/relevancy. Uses ragas when available; else heuristic."""
    try:
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, faithfulness
        from datasets import Dataset

        ds = Dataset.from_dict(
            {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts],
            }
        )
        result = evaluate(ds, metrics=[faithfulness, answer_relevancy])
        scores = {k: float(v) for k, v in dict(result).items() if isinstance(v, (int, float))}
        avg = sum(scores.values()) / max(len(scores), 1)
        return RagasResult(
            ok=avg >= threshold,
            scores=scores,
            findings=[] if avg >= threshold else [f"ragas avg {avg:.2f} < {threshold}"],
        )
    except Exception:
        return _heuristic(question, answer, contexts, threshold)


def _heuristic(question: str, answer: str, contexts: list[str], threshold: float) -> RagasResult:
    ctx = " ".join(contexts).lower()
    ans = answer.lower()
    q_terms = {t for t in question.lower().split() if len(t) > 3}
    overlap = len([t for t in q_terms if t in ans]) / max(len(q_terms), 1)
    grounded = 0.8 if any(chunk.lower()[:40] in ans for chunk in contexts if chunk) or ctx else 0.4
    scores = {"faithfulness": grounded, "answer_relevancy": overlap}
    avg = sum(scores.values()) / 2
    return RagasResult(
        ok=avg >= threshold,
        scores=scores,
        findings=[] if avg >= threshold else [f"heuristic rag score {avg:.2f} < {threshold}"],
    )
