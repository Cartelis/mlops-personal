"""Adversarial robustness regression test."""
import json
import subprocess
import sys

MAX_FLIP_RATE = 0.15


def test_adversarial_flip_rate_bounded():
    proc = subprocess.run(
        [sys.executable, "scripts/adversarial_probe.py", "--samples", "100"],
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    assert report["flip_rate"] <= MAX_FLIP_RATE
    assert report["adversarial_accuracy"] >= 0.85