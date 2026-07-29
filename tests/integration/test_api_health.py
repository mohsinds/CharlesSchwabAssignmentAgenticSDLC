"""API health smoke."""

from fastapi.testclient import TestClient

from services.api.main import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dag_meta():
    client = TestClient(app)
    r = client.get("/pipelines/meta/dag")
    assert r.status_code == 200
    assert "stages" in r.json()
