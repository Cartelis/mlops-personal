"""Model quality slice and fairness checks."""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, recall_score

ROOT = Path(__file__).resolve().parents[1]
SLICE_MIN_ACCURACY = 0.85
MAX_TPR_GAP = 0.08  # lab synthetic data; production target NFR-05: 0.05


def slice_metrics(
    df: pd.DataFrame,
    model,
    feature: str = "f0",
    n_bins: int = 4,
) -> list[dict]:
    features = [c for c in df.columns if c.startswith("f")]
    x = df[features]
    y = df["target"]
    preds = model.predict(x)

    bins = pd.qcut(df[feature], q=n_bins, duplicates="drop")
    slices: list[dict] = []
    for interval in bins.unique():
        mask = bins == interval
        y_slice = y[mask]
        pred_slice = preds[mask]
        slices.append({
            "slice": str(interval),
            "feature": feature,
            "rows": int(mask.sum()),
            "accuracy": float(accuracy_score(y_slice, pred_slice)),
            "recall": float(recall_score(y_slice, pred_slice, zero_division=0)),
        })
    return slices


def fairness_tpr_gap(slices: list[dict]) -> float:
    recalls = [s["recall"] for s in slices if s["rows"] > 0]
    if len(recalls) < 2:
        return 0.0
    return float(max(recalls) - min(recalls))


def evaluate_model_quality(
    model_path: Path | None = None,
    test_path: Path | None = None,
) -> dict:
    model_path = model_path or ROOT / "models" / "model.pkl"
    test_path = test_path or ROOT / "data" / "processed" / "test.csv"
    model = joblib.load(model_path)
    df = pd.read_csv(test_path)

    features = [c for c in df.columns if c.startswith("f")]
    preds = model.predict(df[features])
    overall_acc = float(accuracy_score(df["target"], preds))
    slices = slice_metrics(df, model)
    tpr_gap = fairness_tpr_gap(slices)

    return {
        "overall_accuracy": overall_acc,
        "slices": slices,
        "tpr_gap": round(tpr_gap, 4),
        "slice_min_accuracy": round(min(s["accuracy"] for s in slices), 4),
        "passes_slice_gate": all(s["accuracy"] >= SLICE_MIN_ACCURACY for s in slices),
        "passes_fairness_gate": tpr_gap <= MAX_TPR_GAP,
    }