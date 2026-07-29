"""Unit tests for DAG loader."""

from pathlib import Path

from services.orchestrator.dag_loader import load_dag

ROOT = Path(__file__).resolve().parents[2]


def test_load_dag_validates_and_has_stages():
    dag = load_dag(ROOT / "dag" / "sdlc.yaml", ROOT / "dag" / "schema.json")
    assert dag.name
    assert "classify" in dag.stages
    assert "release_review" in dag.stages
    assert dag.entry_stage().id == "classify"


def test_on_result_branching():
    dag = load_dag(ROOT / "dag" / "sdlc.yaml", ROOT / "dag" / "schema.json")
    assert dag.successors("classify", "ambiguous") == ["clarify"]
    assert dag.successors("classify", "greenfield") == ["requirement"]
    assert dag.successors("classify", "brownfield") == ["codebase_ingest"]


def test_replan_targets():
    dag = load_dag(ROOT / "dag" / "sdlc.yaml", ROOT / "dag" / "schema.json")
    assert "requirement" in dag.replan_targets()
