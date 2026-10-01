"""Benchmark cloud pickle vs ONNX vs edge-quantized ONNX inference."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import onnxruntime as ort
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = 500


def _p95(times_ms: list[float]) -> float:
    if not times_ms:
        return 0.0
    sorted_t = sorted(times_ms)
    idx = max(0, int(len(sorted_t) * 0.95) - 1)
    return sorted_t[idx]


def benchmark_pickle(model_path: Path, x: np.ndarray) -> dict:
    model = joblib.load(model_path)
    times = []
    for row in x:
        start = time.perf_counter()
        model.predict(row.reshape(1, -1))
        times.append((time.perf_counter() - start) * 1000)
    return {
        "backend": "sklearn-pickle",
        "size_bytes": model_path.stat().st_size,
        "p95_ms": round(_p95(times), 3),
        "mean_ms": round(float(np.mean(times)), 3),
    }


def benchmark_onnx(model_path: Path, x: np.ndarray) -> dict:
    session = ort.InferenceSession(str(model_path))
    input_name = session.get_inputs()[0].name
    times = []
    for row in x:
        start = time.perf_counter()
        session.run(None, {input_name: row.reshape(1, -1).astype(np.float32)})
        times.append((time.perf_counter() - start) * 1000)
    return {
        "backend": model_path.name,
        "size_bytes": model_path.stat().st_size,
        "p95_ms": round(_p95(times), 3),
        "mean_ms": round(float(np.mean(times)), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/edge-benchmark.json")
    args = parser.parse_args()

    test = pd.read_csv(ROOT / "data/processed/test.csv")
    feature_cols = [c for c in test.columns if c.startswith("f")]
    x = test[feature_cols].head(SAMPLES).to_numpy()

    results = []
    pkl = ROOT / "models" / "model.pkl"
    onnx = ROOT / "models" / "model.onnx"
    edge = ROOT / "models" / "model.edge.onnx"

    if pkl.exists():
        results.append(benchmark_pickle(pkl, x))
    if onnx.exists():
        results.append(benchmark_onnx(onnx, x))
    if edge.exists():
        results.append(benchmark_onnx(edge, x))

    report = {"samples": len(x), "results": results}
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()