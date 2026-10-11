"""Tests for data contract validation."""

import pandas as pd

from validation.data_contract import run_contract, validate_dataframe


def test_train_test_contract_passes():
    report = run_contract()
    assert report["expectations_total"] >= 10
    assert report["success"] is True


def test_contract_detects_bad_target():
    df = pd.read_csv("data/processed/train.csv").head(200).copy()
    df.loc[0, "target"] = 99
    results = validate_dataframe(df, "synthetic")
    failed = [r for r in results if not r.passed]
    assert any("target_binary" in r.name for r in failed)