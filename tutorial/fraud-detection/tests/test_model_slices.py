"""Model slice and fairness quality tests."""
import json

from validation.model_quality import evaluate_model_quality

ACCURACY_GATE = 0.95
SLICE_MIN = 0.85
MAX_TPR_GAP = 0.08


def test_overall_accuracy_gate():
    report = evaluate_model_quality()
    assert report["overall_accuracy"] >= ACCURACY_GATE


def test_slice_accuracy_floor():
    report = evaluate_model_quality()
    assert report["passes_slice_gate"] is True
    for slice_info in report["slices"]:
        assert slice_info["accuracy"] >= SLICE_MIN


def test_fairness_tpr_gap():
    report = evaluate_model_quality()
    assert report["tpr_gap"] <= MAX_TPR_GAP


def test_metrics_json_matches_gate():
    with open("metrics.json") as f:
        metrics = json.load(f)
    assert metrics["accuracy"] >= ACCURACY_GATE