"""Structured JSON logging for fraud detection API."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

_SKIP = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "module", "msecs",
    "message", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
})


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _SKIP and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, default=str)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log_request(
    logger: logging.Logger,
    method: str,
    endpoint: str,
    status: int,
    duration_s: float,
) -> None:
    logger.info(
        "request_completed",
        extra={
            "event": "request_completed",
            "method": method,
            "endpoint": endpoint,
            "status": status,
            "duration_ms": round(duration_s * 1000, 2),
        },
    )