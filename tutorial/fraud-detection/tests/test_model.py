"""Model quality unit tests."""
import json

import joblib
import pandas as pd
import pytest


@pytest.fixture
def model():
    return joblib.load("models/model.pkl")


def test_model_predicts_binary(model):
    row = pd.DataFrame([[0.1] * 10], columns=[f"f{i}" for i in range(10)])
    pred = model.predict(row)
    assert pred[0] in (0, 1)


def test_metrics_file_exists_and_valid():
    with open("metrics.json") as f:
        metrics = json.load(f)
    assert "accuracy" in metrics
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert metrics["accuracy"] >= 0.5