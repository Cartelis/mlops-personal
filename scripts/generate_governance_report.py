"""Aggregate governance artefacts into a single JSON report."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from governance.checklist import critical_pass_rate, run_checklist, write_checklist
from governance.model_card import REQUIRED_SECTIONS, section_count, write_model_card

CRITICAL_NFR_PATTERN = re.compile(r"NFR-\d+")


def traceability_coverage(path: Path) -> dict:
    if not path.exists():
        return {"rows": 0, "critical_nfrs": 0, "coverage_ratio": 0.0}
    text = path.read_text(encoding="utf-8")
    nfrs = set(CRITICAL_NFR_PATTERN.findall(text))
    rows = len([line for line in text.splitlines() if line.strip().startswith("| NFR-")])
    # Denominator: documented critical NFRs in traceability (at least 15 for capstone)
    denominator = max(len(nfrs), 15)
    return {
        "rows": rows,
        "critical_nfrs": len(nfrs),
        "coverage_ratio": round(len(nfrs) / denominator, 4),
    }


def governance_doc_ok(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "has_risk_tier": False, "has_mitigations": False}
    text = path.read_text(encoding="utf-8").lower()
    return {
        "exists": True,
        "has_risk_tier": "risk" in text and ("high-risk" in text or "tier" in text),
        "has_mitigations": "mitigation" in text or "human oversight" in text,
    }


def security_audit_summary(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "overall_pass": False}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "overall_pass": bool(data.get("overall_pass")),
        "model_watermark": data.get("model_watermark", {}).get("ok"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/governance-report.json")
    parser.add_argument("--min-sections", type=int, default=8)
    parser.add_argument("--min-coverage", type=float, default=0.9)
    parser.add_argument("--min-checklist", type=float, default=1.0)
    args = parser.parse_args()

    model_card_path = write_model_card()
    checklist_path = write_checklist()
    model_card_text = model_card_path.read_text(encoding="utf-8")
    sections = section_count(model_card_text)
    checklist_items = run_checklist()
    checklist_rate = critical_pass_rate(checklist_items)
    trace = traceability_coverage(ROOT / "docs" / "traceability.md")
    gov_doc = governance_doc_ok(ROOT / "docs" / "governance.md")
    security = security_audit_summary(ROOT / "docs" / "security-audit.json")

    gates = {
        "model_card_sections": sections >= args.min_sections,
        "required_sections_present": sections == len(REQUIRED_SECTIONS),
        "eu_ai_act_documented": gov_doc["exists"] and gov_doc["has_risk_tier"] and gov_doc["has_mitigations"],
        "traceability_coverage": trace["coverage_ratio"] >= args.min_coverage,
        "capstone_checklist": checklist_rate >= args.min_checklist,
    }
    overall_pass = all(gates.values())

    report = {
        "model_card": {
            "path": str(model_card_path.relative_to(ROOT)),
            "sections": sections,
            "required_sections": len(REQUIRED_SECTIONS),
        },
        "governance_doc": gov_doc,
        "traceability": trace,
        "security_audit": security,
        "capstone_checklist": {
            "path": str(checklist_path.relative_to(ROOT)),
            "items_total": len(checklist_items),
            "items_green": sum(1 for i in checklist_items if i.ok),
            "pass_rate": round(checklist_rate, 4),
        },
        "gates": gates,
        "overall_pass": overall_pass,
    }

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()