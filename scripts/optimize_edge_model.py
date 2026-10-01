"""Export and dynamically quantize ONNX model for edge deployment."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models" / "model.onnx"
TARGET = ROOT / "models" / "model.edge.onnx"
MANIFEST = ROOT / "models" / "edge-manifest.json"


def ensure_base_onnx() -> None:
    if not SOURCE.exists():
        subprocess.run([sys.executable, "scripts/export_onnx.py"], cwd=ROOT, check=True)


def quantize() -> dict:
    ensure_base_onnx()
    from onnxruntime.quantization import QuantType, quantize_dynamic

    quantize_dynamic(
        model_input=str(SOURCE),
        model_output=str(TARGET),
        weight_type=QuantType.QUInt8,
    )
    return {
        "source": str(SOURCE.relative_to(ROOT)),
        "target": str(TARGET.relative_to(ROOT)),
        "source_bytes": SOURCE.stat().st_size,
        "target_bytes": TARGET.stat().st_size,
        "reduction_ratio": round(TARGET.stat().st_size / SOURCE.stat().st_size, 3),
    }


def main() -> None:
    result = quantize()
    manifest = {
        "format": "onnx-int8-dynamic",
        "model_path": result["target"],
        "cloud_model_path": "models/model.pkl",
        "optimization": result,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()