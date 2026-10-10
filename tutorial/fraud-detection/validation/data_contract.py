"""Great Expectations-style data contract for fraud detection datasets."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FEATURES = [f"f{i}" for i in range(10)]
REQUIRED_COLUMNS = FEATURES + ["target"]
MIN_ROWS = 100
FEATURE_MIN = -10.0
FEATURE_MAX = 10.0
MAX_CLASS_IMBALANCE = 0.95


@dataclass
class ExpectationResult:
    name: str
    passed: bool
    details: str


def _check(name: str, passed: bool, details: str) -> ExpectationResult:
    return ExpectationResult(name=name, passed=passed, details=details)


def validate_dataframe(df: pd.DataFrame, dataset_name: str) -> list[ExpectationResult]:
    results: list[ExpectationResult] = []

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    results.append(_check(
        f"{dataset_name}:required_columns",
        not missing_cols,
        "ok" if not missing_cols else f"missing {missing_cols}",
    ))

    results.append(_check(
        f"{dataset_name}:min_rows",
        len(df) >= MIN_ROWS,
        f"rows={len(df)} min={MIN_ROWS}",
    ))

    if "target" in df.columns:
        null_targets = int(df["target"].isna().sum())
        results.append(_check(
            f"{dataset_name}:target_not_null",
            null_targets == 0,
            f"nulls={null_targets}",
        ))
        unique_targets = set(df["target"].dropna().unique().tolist())
        results.append(_check(
            f"{dataset_name}:target_binary",
            unique_targets.issubset({0, 1}),
            f"values={sorted(unique_targets)}",
        ))
        pos_rate = float(df["target"].mean())
        results.append(_check(
            f"{dataset_name}:class_balance",
            (1 - MAX_CLASS_IMBALANCE) <= pos_rate <= MAX_CLASS_IMBALANCE,
            f"positive_rate={pos_rate:.3f}",
        ))

    for col in FEATURES:
        if col not in df.columns:
            continue
        nulls = int(df[col].isna().sum())
        results.append(_check(
            f"{dataset_name}:{col}_not_null",
            nulls == 0,
            f"nulls={nulls}",
        ))
        col_min = float(df[col].min())
        col_max = float(df[col].max())
        in_range = col_min >= FEATURE_MIN and col_max <= FEATURE_MAX
        results.append(_check(
            f"{dataset_name}:{col}_in_range",
            in_range,
            f"min={col_min:.3f} max={col_max:.3f} bounds=[{FEATURE_MIN},{FEATURE_MAX}]",
        ))

    if "f0" in df.columns:
        f0_std = float(df["f0"].std())
        results.append(_check(
            f"{dataset_name}:f0_variance",
            f0_std > 0.01,
            f"std={f0_std:.4f}",
        ))

    return results


def validate_dataset(path: Path) -> list[ExpectationResult]:
    df = pd.read_csv(path)
    return validate_dataframe(df, path.name)


def run_contract(paths: list[Path] | None = None) -> dict:
    if paths is None:
        paths = [
            ROOT / "data/processed/train.csv",
            ROOT / "data/processed/test.csv",
        ]
    all_results: list[ExpectationResult] = []
    for path in paths:
        if not path.exists():
            all_results.append(_check(f"{path.name}:exists", False, "file missing"))
            continue
        all_results.extend(validate_dataset(path))

    passed = sum(1 for r in all_results if r.passed)
    return {
        "expectations_total": len(all_results),
        "expectations_passed": passed,
        "expectations_failed": len(all_results) - passed,
        "success": passed == len(all_results),
        "results": [
            {"name": r.name, "passed": r.passed, "details": r.details}
            for r in all_results
        ],
    }