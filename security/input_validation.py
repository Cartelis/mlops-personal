"""API input validation and PII rejection for fraud detection service."""
from __future__ import annotations

PII_FIELDS = frozenset({"card_number", "email", "ssn", "name", "phone", "address"})
REQUIRED_FEATURES = frozenset(f"f{i}" for i in range(10))
ALLOWED_EXTRA = frozenset({"transaction_id"})


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

    for key in REQUIRED_FEATURES:
        value = payload[key]
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Feature {key} must be numeric")