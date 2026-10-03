"""Week 3 regressions; run after bootstrap.py and export_onnx.py.

The normal run uses models/ and data/ from the tutorial. WEEK3_FIXTURE_ROOT can
point to an isolated bootstrap output directory when reviewing course changes.
"""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(os.environ.get("WEEK3_FIXTURE_ROOT", ROOT))
FEATURES = [f"f{i}" for i in range(10)]


@pytest.fixture(scope="module")
def services():
    old_model = os.environ.get("MODEL_PATH")
    try:
        os.environ["MODEL_PATH"] = str(FIXTURE_ROOT / "models/model.pkl")
        cpu = importlib.import_module("src.serve")
        os.environ["MODEL_PATH"] = str(FIXTURE_ROOT / "models/model.onnx")
        onnx = importlib.import_module("src.serve_onnx")
        with TestClient(cpu.app) as cpu_client, TestClient(onnx.app) as onnx_client:
            yield cpu_client, onnx_client, onnx.session
    finally:
        if old_model is None:
            os.environ.pop("MODEL_PATH", None)
        else:
            os.environ["MODEL_PATH"] = old_model


@pytest.fixture
def payload():
    # Nonuniform values make a feature ordering bug visible.
    return {name: (index - 4) / 3 for index, name in enumerate(FEATURES)}


def test_health_and_cpu_metrics(services):
    cpu, onnx, _ = services
    for client in (cpu, onnx):
        assert client.get("/health").json() == {"status": "ok"}
    metrics = cpu.get("/metrics")
    assert metrics.status_code == 200
    assert "fraud_api_requests_total" in metrics.text


def test_request_order_and_optional_metadata(services, payload):
    cpu, onnx, _ = services
    expected = cpu.post("/predict", json=payload)
    assert expected.status_code == 200
    reversed_payload = dict(reversed(list(payload.items())))
    reversed_payload["transaction_id"] = "week3-regression"
    for client in (cpu, onnx):
        actual = client.post("/predict", json=reversed_payload)
        assert actual.status_code == 200, actual.text
        assert actual.json() == expected.json()


@pytest.mark.parametrize("change", [
    {"f0": "0.1"}, {"f0": True}, {"f0": None}, {"f0": 1e100},
    {"f0": float("nan")}, {"f0": float("inf")}, {"f0": -float("inf")},
    {"email": "student@example.invalid"}, {"unexpected": 1},
])
def test_invalid_feature_values_return_422(services, payload, change):
    payload.update(change)
    for client in services[:2]:
        # Raw JSON also exercises rejection of non-finite JSON extensions.
        response = client.post(
            "/predict", content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422, response.text


@pytest.mark.parametrize("payload", [{"f0": 0.1}, [], "not an object", None])
def test_invalid_shape_returns_422(services, payload):
    for client in services[:2]:
        response = client.post("/predict", json=payload)
        assert response.status_code == 422, response.text


def test_all_bootstrap_holdout_labels_match(services):
    _, _, session = services
    model = joblib.load(FIXTURE_ROOT / "models/model.pkl")
    test = pd.read_csv(FIXTURE_ROOT / "data/processed/test.csv")
    inputs = test[FEATURES].astype(np.float32)
    expected = model.predict(inputs)
    actual = session.run(None, {session.get_inputs()[0].name: inputs.to_numpy()})[0]
    assert len(test) == 200
    np.testing.assert_array_equal(actual, expected)
