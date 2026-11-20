# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "fastapi>=0.110",
#   "uvicorn>=0.29",
#   "prometheus-client>=0.20",
# ]
# ///
"""Week-12 scaling demo: a CPU-bound 'model' and an optional fake feature store.

Run locally:   uv run app.py
Act 1 (default, FEATURE_STORE_MS=0): every request burns CPU -> load shows up as CPU.
Act 2 (FEATURE_STORE_MS=40):         every request first waits for the feature store
                                     -> load shows up as waiting; CPU stays low.
"""
import asyncio
import hashlib
import os
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

MODEL_CPU_MS = float(os.environ.get("MODEL_CPU_MS", "1.5"))  # CPU time of one "model" call
FEATURE_STORE_MS = float(os.environ.get("FEATURE_STORE_MS", "0"))  # 0 = no feature store (Act 1)
FEATURE_STORE_CONNS = int(os.environ.get("FEATURE_STORE_CONNS", "1"))  # client connection pool size

app = FastAPI()
pool = asyncio.Semaphore(FEATURE_STORE_CONNS)  # at most N requests talk to the store at once

REQUESTS = Counter("fraud_api_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram(
    "fraud_api_request_duration_seconds", "Request latency", ["path"],
    buckets=(0.01, 0.025, 0.05, 0.08, 0.1, 0.25, 0.5, 1, 2, 3, 5),
)


def _rounds_per_ms() -> float:
    """Calibrate: how many SHA-256 rounds this CPU does per millisecond."""
    n, h, t0 = 20_000, b"x", time.perf_counter()
    for _ in range(n):
        h = hashlib.sha256(h).digest()
    return n / ((time.perf_counter() - t0) * 1000)


ROUNDS = max(1, int(_rounds_per_ms() * MODEL_CPU_MS))


def model_predict(features: dict) -> int:
    """The 'model': pure CPU work, ~MODEL_CPU_MS per call."""
    h = repr(features).encode()
    for _ in range(ROUNDS):
        h = hashlib.sha256(h).digest()
    return int(h[0] > 250)  # ~2 % "fraud"


@app.middleware("http")
async def observe(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    REQUESTS.labels(request.method, request.url.path, str(response.status_code)).inc()
    LATENCY.labels(request.url.path).observe(time.perf_counter() - start)
    return response


@app.get("/health")
async def health():
    return {"status": "ok", "model_cpu_ms": MODEL_CPU_MS, "feature_store_ms": FEATURE_STORE_MS}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict")
async def predict(features: dict):
    if FEATURE_STORE_MS > 0:
        async with pool:  # wait for a free connection...
            await asyncio.sleep(FEATURE_STORE_MS / 1000)  # ...then for the store: no CPU used
    return {"prediction": model_predict(features)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), access_log=False)
