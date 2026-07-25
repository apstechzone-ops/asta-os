from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
