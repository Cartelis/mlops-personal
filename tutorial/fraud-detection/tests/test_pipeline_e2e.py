"""End-to-end pipeline test: data -> train metrics -> API predict."""
import json
import subprocess
import sys

from fastapi.testclient import TestClient

from src.serve import app


def test_e2e_bootstrap_evaluate_predict():
    subprocess.run([sys.executable, "scripts/bootstrap.py"], check=True)
    subprocess.run([sys.executable, "src/evaluate.py"], check=True)

    with open("metrics.json") as f:
        metrics = json.load(f)
    assert metrics["accuracy"] >= 0.95

    client = TestClient(app)
    payload = {f"f{i}": 0.1 for i in range(10)}
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert "prediction" in response.json()