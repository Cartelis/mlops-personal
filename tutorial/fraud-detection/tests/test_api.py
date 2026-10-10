"""API integration tests."""
from fastapi.testclient import TestClient

from src.serve import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_schema():
    payload = {f"f{i}": 0.1 for i in range(10)}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert "prediction" in response.json()


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "fraud_api_requests_total" in response.text


def test_predict_rejects_pii():
    payload = {f"f{i}": 0.1 for i in range(10)}
    payload["email"] = "user@example.com"
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "PII" in response.json()["detail"]


def test_predict_missing_features():
    response = client.post("/predict", json={"f0": 0.1})
    assert response.status_code == 422