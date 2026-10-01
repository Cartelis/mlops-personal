"""Week 16 governance gates: model card, checklist, report."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from governance.checklist import critical_pass_rate, run_checklist, write_checklist
from governance.model_card import REQUIRED_SECTIONS, section_count, write_model_card


@pytest.fixture(scope="module")
def bootstrapped_model():
    subprocess.run(
        [sys.executable, "scripts/bootstrap.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return ROOT / "models" / "model.pkl"


def test_model_card_has_required_sections(bootstrapped_model):
    path = write_model_card()
    text = path.read_text(encoding="utf-8")
    assert section_count(text) == len(REQUIRED_SECTIONS)
    for title in REQUIRED_SECTIONS:
        assert f"## {title}" in text


def test_capstone_checklist_critical_items(bootstrapped_model):
    write_checklist()
    items = run_checklist()
    assert len(items) >= 12
    assert critical_pass_rate(items) >= 1.0


def test_governance_report_passes(bootstrapped_model):
    result = subprocess.run(
        [sys.executable, "scripts/generate_governance_report.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    report_path = ROOT / "docs" / "governance-report.json"
    data = json.loads(report_path.read_text(encoding="utf-8"))
    assert data["overall_pass"] is True
    assert data["model_card"]["sections"] >= 8
    assert data["traceability"]["coverage_ratio"] >= 0.9