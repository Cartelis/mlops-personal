"""API input validation and PII rejection for fraud detection service."""
from __future__ import annotations

import math

PII_FIELDS = frozenset({"card_number", "email", "ssn", "name", "phone", "address"})
FEATURE_NAMES = tuple(f"f{i}" for i in range(10))
REQUIRED_FEATURES = frozenset(FEATURE_NAMES)
ALLOWED_EXTRA = frozenset({"transaction_id"})
# Both sklearn trees and the exported ONNX graph consume float32 features.
FLOAT32_MAX = 3.4028234663852886e38


class ValidationError(ValueError):
    pass


def validate_predict_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValidationError("payload must be a JSON object")

    pii = PII_FIELDS.intersection(payload.keys())
    if pii:
        raise ValidationError(f"PII fields rejected: {sorted(pii)}")

    unknown = set(payload.keys()) - REQUIRED_FEATURES - ALLOWED_EXTRA
    if unknown:
        raise ValidationError(f"Unknown fields: {sorted(unknown)}")

    missing = REQUIRED_FEATURES - payload.keys()
    if missing:
        raise ValidationError(f"Missing features: {sorted(missing)}")

    for key in FEATURE_NAMES:
        value = payload[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"Feature {key} must be numeric")
        try:
            valid = math.isfinite(value) and abs(value) <= FLOAT32_MAX
        except OverflowError:
            valid = False
        if not valid:
            raise ValidationError(f"Feature {key} must be finite and fit float32")
