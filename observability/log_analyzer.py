"""Parse structured JSON logs and detect latency/error anomalies."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LogSummary:
    total: int
    errors: int
    slow_requests: int
    p95_duration_ms: float


def parse_log_lines(lines: list[str]) -> list[dict]:
    records: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def summarize(records: list[dict], slow_ms: float = 80.0) -> LogSummary:
    durations = [
        float(r["duration_ms"])
        for r in records
        if r.get("event") == "request_completed" and "duration_ms" in r
    ]
    errors = sum(
        1 for r in records
        if r.get("event") == "request_completed" and int(r.get("status", 200)) >= 500
    )
    slow = sum(1 for d in durations if d > slow_ms)
    p95 = 0.0
    if durations:
        sorted_d = sorted(durations)
        idx = max(0, int(len(sorted_d) * 0.95) - 1)
        p95 = sorted_d[idx]
    return LogSummary(total=len(records), errors=errors, slow_requests=slow, p95_duration_ms=p95)


def analyze_stream(stream, slow_ms: float = 80.0, last: int | None = None) -> LogSummary:
    lines = stream.readlines()
    if last is not None:
        lines = lines[-last:]
    return summarize(parse_log_lines(lines), slow_ms=slow_ms)


def analyze_file(path: Path, slow_ms: float = 80.0, last: int | None = None) -> LogSummary:
    lines = path.read_text(encoding="utf-8").splitlines()
    if last is not None:
        lines = lines[-last:]
    return summarize(parse_log_lines(lines), slow_ms=slow_ms)