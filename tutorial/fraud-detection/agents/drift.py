"""Drift detection using feature distribution shift (PSI on f0)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DRIFT_THRESHOLD = 0.25
BASELINE = Path("data/processed/train.csv")
RECENT = Path("data/raw/drift_sample.csv")


def population_stability_index(expected: pd.Series, actual: pd.Series, buckets: int = 10) -> float:
    """Simplified PSI for a single numeric feature."""
    breakpoints = np.linspace(expected.min(), expected.max(), buckets + 1)
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    expected_counts = pd.cut(expected, breakpoints).value_counts(normalize=True).sort_index()
    actual_counts = pd.cut(actual, breakpoints).value_counts(normalize=True).sort_index()

    psi = 0.0
    for bucket in expected_counts.index:
        e = max(expected_counts.get(bucket, 0.0), 1e-6)
        a = max(actual_counts.get(bucket, 0.0), 1e-6)
        psi += (a - e) * np.log(a / e)
    return float(psi)


def check_drift() -> dict:
    if not BASELINE.exists():
        return {"drift_detected": False, "psi": 0.0, "reason": "missing baseline"}

    if not RECENT.exists():
        return {"drift_detected": False, "psi": 0.0, "reason": "no recent data"}

    base = pd.read_csv(BASELINE)
    recent = pd.read_csv(RECENT)
    if "f0" not in base.columns or "f0" not in recent.columns:
        return {"drift_detected": False, "psi": 0.0, "reason": "missing f0"}

    psi = population_stability_index(base["f0"], recent["f0"])
    return {
        "drift_detected": psi > DRIFT_THRESHOLD,
        "psi": round(psi, 4),
        "threshold": DRIFT_THRESHOLD,
        "feature": "f0",
    }


if __name__ == "__main__":
    print(json.dumps(check_drift(), indent=2))