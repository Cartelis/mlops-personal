"""Export the Week 3 sklearn model. Run from tutorial/fraud-detection."""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import onnx
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

FEATURE_NAMES = [f"f{i}" for i in range(10)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("models/model.pkl"))
    parser.add_argument("--output", type=Path, default=Path("models/model.onnx"))
    args = parser.parse_args()
    model = joblib.load(args.input)
    if getattr(model, "n_features_in_", None) != len(FEATURE_NAMES):
        raise ValueError("Week 3 model must have ten features: f0 through f9")
    if list(getattr(model, "feature_names_in_", [])) != FEATURE_NAMES:
        raise ValueError("Model feature order must be f0, f1, ..., f9; rerun bootstrap.py")

    converted = convert_sklearn(
        model,
        initial_types=[("float_input", FloatTensorType([None, len(FEATURE_NAMES)]))],
        options={id(model): {"zipmap": False}},
        target_opset=17,
    )
    onnx.checker.check_model(converted)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(converted.SerializeToString())
    print(f"Exported {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
