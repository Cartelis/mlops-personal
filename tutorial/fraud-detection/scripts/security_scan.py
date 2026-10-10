"""Run Trivy container scan with optional CI fail gate."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys


def run_trivy(image: str, fail_on_critical: bool) -> dict:
    trivy = shutil.which("trivy")
    if not trivy:
        return {
            "status": "skipped",
            "reason": "trivy not installed",
            "image": image,
            "critical": 0,
            "high": 0,
        }

    cmd = [
        trivy, "image", "--format", "json",
        "--severity", "CRITICAL,HIGH",
        image,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr or proc.stdout)

    data = json.loads(proc.stdout or "{}")
    results = data.get("Results", [])
    critical = high = 0
    for result in results:
        for vuln in result.get("Vulnerabilities") or []:
            sev = vuln.get("Severity", "")
            if sev == "CRITICAL":
                critical += 1
            elif sev == "HIGH":
                high += 1

    status = "pass"
    if fail_on_critical and critical > 0:
        status = "fail"

    return {
        "status": status,
        "image": image,
        "critical": critical,
        "high": high,
        "scanner": "trivy",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="mlops-cpu:local")
    parser.add_argument("--fail-on-critical", action="store_true")
    args = parser.parse_args()
    result = run_trivy(args.image, args.fail_on_critical)
    print(json.dumps(result, indent=2))
    if result["status"] == "fail":
        sys.exit(1)


if __name__ == "__main__":
    main()