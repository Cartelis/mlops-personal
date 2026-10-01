"""Correlate metrics, drift report, and log anomalies for AIOps demo."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LATENCY_SLO_S = 0.08
DRIFT_THRESHOLD = 0.25


def parse_histogram_p95(metrics_text: str, metric: str) -> float | None:
    buckets: dict[float, float] = {}
    for line in metrics_text.splitlines():
        if metric not in line or "le=" not in line:
            continue
        match = re.search(r'le="([^"]+)".*? (\d+(?:\.\d+)?(?:e[+-]?\d+)?)$', line)
        if match:
            le = match.group(1)
            val = float(match.group(2))
            if le == "+Inf":
                continue
            buckets[float(le)] = val
    if not buckets:
        return None
    # Approximate p95 from cumulative bucket counts (lab simplification)
    total = max(buckets.values())
    if total <= 0:
        return 0.0
    target = total * 0.95
    for le in sorted(buckets):
        if buckets[le] >= target:
            return le
    return max(buckets)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-url", default="http://127.0.0.1:8080/metrics")
    parser.add_argument("--drift-report", default="docs/drift-report.json")
    args = parser.parse_args()

    drift_path = ROOT / args.drift_report
    drift = json.loads(drift_path.read_text()) if drift_path.exists() else {}
    psi = float(drift.get("max_psi", 0))
    drift_detected = bool(drift.get("drift_detected", False))

    metrics_text = httpx.get(args.metrics_url, timeout=5.0).text
    p95 = parse_histogram_p95(metrics_text, "fraud_api_request_duration_seconds_bucket")
    high_latency = p95 is not None and p95 > LATENCY_SLO_S

    psi_match = re.search(r"^fraud_drift_psi (\S+)", metrics_text, re.MULTILINE)
    if psi_match:
        psi = float(psi_match.group(1))

    triggers = []
    if drift_detected or psi > DRIFT_THRESHOLD:
        triggers.append("drift")
    if high_latency:
        triggers.append("high_latency")

    recommendation = "monitor"
    if "drift" in triggers and "high_latency" in triggers:
        recommendation = "trigger_self_healing_agent"
    elif "drift" in triggers:
        recommendation = "investigate_drift_then_consider_agent"
    elif "high_latency" in triggers:
        recommendation = "check_infra_scaling"

    result = {
        "correlated_signals": triggers,
        "psi": psi,
        "p95_latency_s": p95,
        "recommendation": recommendation,
        "suggested_command": (
            "python -m agents.mlops_agent --incident-id DR-AIOPS-001"
            if recommendation == "trigger_self_healing_agent"
            else None
        ),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()