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
from security.input_validation import FEATURE_NAMES, ValidationError, validate_predict_payload

app = FastAPI()
logger = get_logger("fraud-api")

# Where the model comes from (week 9): MODEL_URI points at the registry, e.g. models:/fraud-detector@champion,
# and the service loads it through MLflow at start-up; without MODEL_URI the week-3 behaviour stays -
# the pickle at MODEL_PATH baked into the image.
MODEL_URI = os.environ.get("MODEL_URI")
MODEL_PATH = os.environ.get("MODEL_PATH", str(ROOT / "models/model.pkl"))
MODEL_INFO: dict = {"source": MODEL_URI or MODEL_PATH}


def _load_model():
    if MODEL_URI:
        import mlflow                       # only needed in the registry-backed deployment
        from mlflow import MlflowClient

        loaded = mlflow.sklearn.load_model(MODEL_URI)
        if MODEL_URI.startswith("models:/") and "@" in MODEL_URI:
            name, alias = MODEL_URI[len("models:/"):].split("@", 1)
            mv = MlflowClient().get_model_version_by_alias(name, alias)
            MODEL_INFO.update({"model": name, "alias": alias, "version": int(mv.version), "run_id": mv.run_id})
        return loaded
    return joblib.load(MODEL_PATH)


try:
    model = _load_model()
except Exception as exc:  # noqa: BLE001 - a missing champion is a normal state before the first promotion
    model = None
    MODEL_INFO["error"] = str(exc)
    logger.warning("model not loaded (%s): /health reports 'no model' until a restart finds one", exc)

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
    if model is None:
        raise HTTPException(status_code=503, detail={"status": "no model", **MODEL_INFO})
    return {"status": "ok", **MODEL_INFO}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict")
def predict(features: dict):
    if model is None:
        raise HTTPException(status_code=503, detail={"status": "no model", **MODEL_INFO})
    try:
        validate_predict_payload(features)
    except ValidationError as exc:
        VALIDATION_ERRORS.labels(reason=type(exc).__name__).inc()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # JSON object order is not a model feature order. Ignore allowed metadata.
    df = pd.DataFrame([[features[name] for name in FEATURE_NAMES]], columns=FEATURE_NAMES)
    pred = model.predict(df)
    pred_int = int(pred[0])
    PREDICTION_COUNT.labels(str(pred_int)).inc()
    log_inference(features, pred_int)
    return {"prediction": pred_int}
