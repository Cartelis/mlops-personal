"""Inference audit logging without storing PII."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_LOG = ROOT / "docs" / "inference-audit.log"
MODEL_VERSION = "v1.2.0"


def _feature_hash(payload: dict) -> str:
    features = {k: payload[k] for k in sorted(payload) if k.startswith("f")}
    blob = json.dumps(features, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def log_inference(payload: dict, prediction: int, model_version: str = MODEL_VERSION) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "inference_audit",
        "prediction": prediction,
        "feature_hash": _feature_hash(payload),
        "model_version": model_version,
        "transaction_id_present": "transaction_id" in payload,
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")