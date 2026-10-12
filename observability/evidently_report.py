"""Generate drift report comparing baseline train data vs recent production sample."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "data/processed/train.csv"
RECENT = ROOT / "data/raw/drift_sample.csv"
DRIFT_THRESHOLD = 0.25


def population_stability_index(expected: pd.Series, actual: pd.Series, buckets: int = 10) -> float:
    breakpoints = np.linspace(expected.min(), expected.max(), buckets + 1)
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf
    expected_counts = pd.cut(expected, breakpoints).value_counts(normalize=True).sort_index()
    actual_counts = pd.cut(actual, breakpoints).value_counts(normalize=True).sort_index()
    psi = 0.0
    for bucket in expected_counts.index:
        e = max(float(expected_counts.get(bucket, 0.0)), 1e-6)
        a = max(float(actual_counts.get(bucket, 0.0)), 1e-6)
        psi += (a - e) * np.log(a / e)
    return float(psi)


def build_report() -> dict:
    if not BASELINE.exists():
        return {"drift_detected": False, "reason": "missing baseline", "features": {}}
    if not RECENT.exists():
        return {"drift_detected": False, "reason": "missing recent sample", "features": {}}

    base = pd.read_csv(BASELINE)
    recent = pd.read_csv(RECENT)
    feature_cols = [c for c in base.columns if c.startswith("f")]

    features: dict[str, dict] = {}
    max_psi = 0.0
    for col in feature_cols:
        if col not in recent.columns:
            continue
        psi = population_stability_index(base[col], recent[col])
        max_psi = max(max_psi, psi)
        features[col] = {"psi": round(psi, 4), "drift_detected": psi > DRIFT_THRESHOLD}

    drift_detected = max_psi > DRIFT_THRESHOLD
    report = {
        "drift_detected": drift_detected,
        "max_psi": round(max_psi, 4),
        "threshold": DRIFT_THRESHOLD,
        "features": features,
        "baseline_rows": len(base),
        "recent_rows": len(recent),
    }

    try:
        from evidently import Report
        from evidently.presets import DataDriftPreset

        html_path = ROOT / "docs" / "drift-report.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = Report([DataDriftPreset()]).run(
            base[feature_cols], recent[feature_cols]
        )
        snapshot.save_html(str(html_path))
        report["evidently_html"] = str(html_path)
    except Exception as exc:    # noqa: BLE001
        report["evidently_note"] = f"HTML report skipped: {exc}"

    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/drift-report.json")
    args = parser.parse_args()
    report = build_report()
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()