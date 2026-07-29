"""Classifier heuristic tests."""

import pytest

from services.agents.graphs.classifier_graph import run
from services.agents.nodes.llm import classify_heuristic


def test_heuristic_greenfield():
    r = classify_heuristic("Build a URL shortener with POST /shorten and analytics")
    assert r["classification"] == "greenfield"


def test_heuristic_brownfield():
    r = classify_heuristic("Add rate limiting and Redis cache to the existing service")
    assert r["classification"] == "brownfield"


def test_heuristic_ambiguous():
    r = classify_heuristic("Make the URL shortener enterprise-ready")
    assert r["classification"] == "ambiguous"
    assert r["questions"]


@pytest.mark.asyncio
async def test_classifier_run_fallback():
    out = await run(
        {
            "run_id": "t1",
            "trace_id": "t1",
            "stage_id": "classify",
            "prompt": "Build a URL shortener API",
            "mode": "live",
        }
    )
    assert out["classification"] in {"greenfield", "brownfield", "ambiguous"}
    assert "structured" in out
