"""FastAPI inference server for ONNX model."""
import os
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, HTTPException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from security.input_validation import (
    FEATURE_NAMES,
    ValidationError,
    validate_predict_payload,
)

app = FastAPI()
session = ort.InferenceSession(
    os.environ.get("MODEL_PATH", str(ROOT / "models/model.onnx")),
    providers=["CPUExecutionProvider"],
)
input_name = session.get_inputs()[0].name


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(features: dict):
    try:
        validate_predict_payload(features)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    row = np.array([[features[name] for name in FEATURE_NAMES]], dtype=np.float32)
    label = session.run(None, {input_name: row})[0]
    return {"prediction": int(label[0])}
