"""Probe model robustness with small feature perturbations (evasion demo)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def probe(model_path: Path, samples: int, epsilon: float) -> dict:
    model = joblib.load(model_path)
    test = pd.read_csv(ROOT / "data/processed/test.csv")
    feature_cols = [c for c in test.columns if c.startswith("f")]
    x = test[feature_cols].head(samples).copy()
    y = test["target"].head(samples).values

    base_pred = model.predict(x)
    base_acc = float((base_pred == y).mean())

    rng = np.random.default_rng(42)
    x_adv = x.copy()
    for col in feature_cols:
        x_adv[col] = x_adv[col] + rng.uniform(-epsilon, epsilon, size=len(x_adv))

    adv_pred = model.predict(x_adv)
    adv_acc = float((adv_pred == y).mean())
    flips = int((base_pred != adv_pred).sum())

    return {
        "samples": samples,
        "epsilon": epsilon,
        "baseline_accuracy": round(base_acc, 4),
        "adversarial_accuracy": round(adv_acc, 4),
        "prediction_flips": flips,
        "flip_rate": round(flips / samples, 4),
        "note": "Small perturbations demonstrate evasion risk; mitigate with validation bounds",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/model.pkl")
    parser.add_argument("--samples", type=int, default=100)
    parser.add_argument("--epsilon", type=float, default=0.5)
    args = parser.parse_args()
    result = probe(ROOT / args.model, args.samples, args.epsilon)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()