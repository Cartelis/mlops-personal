"""FastAPI inference server for sklearn model (CPU Docker image)."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from observability.logging_config import get_logger, log_request
from security.inference_audit import log_inference
from security.input_validation import ValidationError, validate_predict_payload

app = FastAPI()
model = joblib.load(os.environ.get("MODEL_PATH", "models/model.pkl"))
logger = get_logger("fraud-api")

REQUEST_COUNT = Counter(
    "fraud_api_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "fraud_api_request_duration_seconds",
    "Request latency in seconds",
    ["endpoint"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
PREDICTION_COUNT = Counter(
    "fraud_predictions_total",
    "Predictions by class label",
    ["prediction"],
)
VALIDATION_ERRORS = Counter(
    "fraud_api_validation_errors_total",
    "Rejected requests at validation layer",
    ["reason"],
)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    endpoint = request.url.path
    REQUEST_COUNT.labels(request.method, endpoint, str(response.status_code)).inc()
    if endpoint in ("/predict", "/health", "/metrics"):
        REQUEST_LATENCY.labels(endpoint).observe(duration)
    log_request(logger, request.method, endpoint, response.status_code, duration)
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict")
def predict(features: dict):
    try:
        validate_predict_payload(features)
    except ValidationError as exc:
        VALIDATION_ERRORS.labels(reason=type(exc).__name__).inc()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    df = pd.DataFrame([features])
    pred = model.predict(df)
    pred_int = int(pred[0])
    PREDICTION_COUNT.labels(str(pred_int)).inc()
    log_inference(features, pred_int)
    return {"prediction": pred_int}