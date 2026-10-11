"""Aggregate local security checks into audit report JSON."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from security.watermark import verify_watermark


def check_policies() -> dict:
    policy_dir = ROOT / "security" / "policies"
    files = sorted(policy_dir.glob("*.yaml")) if policy_dir.exists() else []
    return {
        "policy_files": len(files),
        "paths": [str(p.relative_to(ROOT)) for p in files],
        "meets_minimum": len(files) >= 3,
    }


def check_ci_workflow() -> dict:
    workflow = ROOT / ".github" / "workflows" / "security.yml"
    return {"exists": workflow.exists(), "path": str(workflow.relative_to(ROOT))}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/security-audit.json")
    args = parser.parse_args()

    from scripts.generate_sbom import generate_sbom
    from scripts.security_scan import run_trivy

    sbom_path = ROOT / "docs" / "sbom-cpu.json"
    report = {
        "gatekeeper_policies": check_policies(),
        "ci_security_workflow": check_ci_workflow(),
        "trivy_scan": run_trivy("mlops-cpu:local", fail_on_critical=False),
        "sbom": generate_sbom("mlops-cpu:local", sbom_path),
        "model_watermark": verify_watermark(ROOT / "models" / "model.pkl"),
        "network_policy": (ROOT / "k8s" / "network-policy-fraud-api.yaml").exists(),
        "inference_audit_log": (ROOT / "docs" / "inference-audit.log").exists(),
    }
    report["overall_pass"] = (
        report["gatekeeper_policies"]["meets_minimum"]
        and report["ci_security_workflow"]["exists"]
        and report["network_policy"]
    )

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()