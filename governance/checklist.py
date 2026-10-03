"""Capstone readiness checklist for week 16 governance lab."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CRITICAL_ITEMS = [
    ("model_trained", "Trained model artefact", "models/model.pkl"),
    ("metrics_present", "Evaluation metrics", "metrics.json"),
    ("requirements_doc", "Living requirements", "docs/requirements.md"),
    ("traceability_matrix", "NFR traceability", "docs/traceability.md"),
    ("model_card", "Model card", "docs/model-card.md"),
    ("governance_doc", "EU AI Act assessment", "docs/governance.md"),
    ("ci_pipeline", "CI workflow", ".github/workflows/ml-pipeline.yml"),
    ("test_suite", "Automated tests", "tests/test_pipeline_e2e.py"),
    ("data_contract", "Data validation", "validation/data_contract.py"),
    ("security_policies", "Gatekeeper policies", "security/policies"),
    ("observability_stack", "Monitoring config", "monitoring/prometheus.yml"),
    ("serve_module", "API serving", "src/serve.py"),
]


@dataclass
class ChecklistItem:
    key: str
    label: str
    path: str
    ok: bool
    detail: str


def evaluate_item(key: str, label: str, rel_path: str) -> ChecklistItem:
    path = ROOT / rel_path
    if rel_path.endswith("/") or not path.suffix:
        ok = path.is_dir() and any(path.iterdir()) if path.exists() else False
        detail = "directory missing or empty" if not ok else "ok"
    else:
        ok = path.is_file()
        detail = "missing" if not ok else "ok"
    return ChecklistItem(key=key, label=label, path=rel_path, ok=ok, detail=detail)


def run_checklist() -> list[ChecklistItem]:
    return [evaluate_item(k, label, p) for k, label, p in CRITICAL_ITEMS]


def critical_pass_rate(items: list[ChecklistItem] | None = None) -> float:
    items = items or run_checklist()
    if not items:
        return 0.0
    passed = sum(1 for i in items if i.ok)
    return passed / len(items)


def render_markdown(items: list[ChecklistItem] | None = None) -> str:
    items = items or run_checklist()
    lines = [
        "# Capstone Readiness Checklist — Week 16",
        "",
        f"**Critical items:** {sum(1 for i in items if i.ok)}/{len(items)} green",
        "",
        "| Item | Path | Status |",
        "|------|------|--------|",
    ]
    for item in items:
        status = "green" if item.ok else "red"
        lines.append(f"| {item.label} | `{item.path}` | {status} |")
    lines.extend(
        [
            "",
            "## Pre-demo commands",
            "",
            "```bash",
            "python scripts/bootstrap.py",
            "pytest tests/ -v",
            "python scripts/generate_governance_report.py",
            "python -m uvicorn src.serve:app --port 8080",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def write_checklist(output: Path | None = None) -> Path:
    output = output or ROOT / "docs" / "capstone-checklist.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(), encoding="utf-8")
    return output