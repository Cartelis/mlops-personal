"""Tool implementations for the self-healing MLOps agent."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
AUDIT_LOG = ROOT / "docs" / "agent-audit.log"
SLACK_MOCK = ROOT / "docs" / "slack-mock.txt"
MAX_RETRAINS_FILE = ROOT / "docs" / "agent-retrain-count.json"
MAX_RETRAINS_PER_DAY = 3
ACCURACY_GATE = 0.95


def audit(action: str, details: dict) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "action": action,
        **details,
    }
    with open(AUDIT_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _retrain_count_today() -> int:
    if not MAX_RETRAINS_FILE.exists():
        return 0
    data = json.loads(MAX_RETRAINS_FILE.read_text())
    today = datetime.now(UTC).date().isoformat()
    return int(data.get(today, 0))


def _increment_retrain_count() -> None:
    today = datetime.now(UTC).date().isoformat()
    data = {}
    if MAX_RETRAINS_FILE.exists():
        data = json.loads(MAX_RETRAINS_FILE.read_text())
    data[today] = int(data.get(today, 0)) + 1
    MAX_RETRAINS_FILE.write_text(json.dumps(data, indent=2))


def tool_check_drift() -> dict:
    from agents.drift import check_drift

    result = check_drift()
    audit("check_drift", result)
    return result


def tool_run_retrain(approve: bool = True) -> dict:
    count = _retrain_count_today()
    if count >= MAX_RETRAINS_PER_DAY:
        result = {"status": "blocked", "reason": "max_retrains_per_day"}
        audit("retrain", result)
        return result

    cmd = [sys.executable, "pipeline/ray_pipeline.py", "--run-id", "agent-retrain"]
    if approve:
        cmd.append("--approve")
    subprocess.run(cmd, cwd=ROOT, check=True)
    _increment_retrain_count()
    result = {"status": "retrain_ok", "retrains_today": count + 1}
    audit("retrain", result)
    return result


def tool_read_metrics() -> dict:
    metrics_path = ROOT / "metrics.json"
    with open(metrics_path) as f:
        metrics = json.load(f)
    audit("read_metrics", metrics)
    return metrics


def tool_model_gate(metrics: dict) -> dict:
    accuracy = metrics.get("accuracy", 0)
    passed = accuracy >= ACCURACY_GATE
    result = {"passed": passed, "accuracy": accuracy, "threshold": ACCURACY_GATE}
    audit("model_gate", result)
    return result


def tool_deploy() -> dict:
    result = {"status": "deploy_triggered", "method": "gitops"}
    audit("deploy", result)
    return result


def tool_notify_slack(message: str) -> dict:
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        SLACK_MOCK.parent.mkdir(parents=True, exist_ok=True)
        SLACK_MOCK.write_text(message + "\n", encoding="utf-8")
        result = {"status": "mock_written", "path": str(SLACK_MOCK)}
    else:
        httpx.post(webhook, json={"text": message}, timeout=10.0)
        result = {"status": "sent"}
    audit("notify", {"message": message[:500], **result})
    return result