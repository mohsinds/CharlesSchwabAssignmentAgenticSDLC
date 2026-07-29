"""Scoring / deterministic judge tests."""

from services.judge.deterministic import check_ast
from services.judge.scoring import composite_score
from services.judge.deterministic import DeterministicResult
from services.judge.llm_judge import LLMJudgeResult


def test_ast_ok():
    r = check_ast("def f(x):\n    return x + 1\n")
    assert r.ok


def test_ast_fail():
    r = check_ast("def f(:\n")
    assert not r.ok


def test_composite_never_overrides_deterministic():
    score = composite_score(
        deterministic=DeterministicResult(ok=False, findings=["syntax"]),
        llm=LLMJudgeResult(ok=True, score=0.99, rationale="looks fine", dimensions={}),
    )
    assert score.passed is False
    assert score.deterministic_ok is False
