"""Generate a model card markdown document from project artefacts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SECTIONS = [
    "Model Details",
    "Intended Use",
    "Factors",
    "Metrics",
    "Training Data",
    "Evaluation Data",
    "Ethical Considerations",
    "Caveats and Recommendations",
]


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_model_card(
    metrics_path: Path | None = None,
    manifest_path: Path | None = None,
) -> str:
    metrics_path = metrics_path or ROOT / "metrics.json"
    manifest_path = manifest_path or ROOT / "models" / "model.pkl.manifest.json"
    metrics = _load_json(metrics_path)
    manifest = _load_json(manifest_path)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    accuracy = metrics.get("accuracy", "N/A")
    f1 = metrics.get("f1", "N/A")
    owner = manifest.get("owner", "mlops-team")
    model_version = manifest.get("version", "1.0.0")

    return f"""# Model Card — Fraud Detection Classifier

## Model Details

- **Model name:** fraud-detection-rf
- **Version:** {model_version}
- **Owner:** {owner}
- **Architecture:** scikit-learn RandomForest (tabular)
- **Generated:** {generated}

## Intended Use

- **Primary use:** Real-time fraud scoring for card transactions via `POST /predict`.
- **Users:** Internal fraud operations and payment routing services.
- **Out of scope:** Credit underwriting, employment decisions, or any use without human review for account closure.

## Factors

- Trained on synthetic tabular features (`f0`–`f9`); performance may differ on production distributions.
- Requires periodic drift monitoring (Evidently) and slice fairness checks (NFR-05).
- Edge deployment uses quantized ONNX variant (week 14).

## Metrics

| Metric | Value | Target (NFR) |
|--------|-------|--------------|
| Accuracy | {accuracy} | >= 0.95 (NFR-60) |
| F1 | {f1} | — |
| Recall | see slice tests | >= 0.92 (NFR-02) |

## Training Data

- **Source:** `data/raw/train.csv` (synthetic bootstrap).
- **Features:** `f0`–`f9` (numeric, no PII).
- **Target:** binary fraud label `0/1`.
- **Validation:** data contract suite (`validation/data_contract.py`).

## Evaluation Data

- **Hold-out:** `data/raw/test.csv`.
- **Method:** `src/evaluate.py` writes `metrics.json`.
- **Slice evaluation:** `validation/model_quality.py` quartile bins on `f0`.

## Ethical Considerations

- Fairness proxy: TPR gap across slices <= 8% (test gate; production target 5% per NFR-05).
- PII fields rejected at API boundary (`tests/test_api.py`).
- Inference audit log records prediction metadata without raw PII.

## Caveats and Recommendations

- Do not deploy without passing `pytest tests/ -v` and `scripts/check_model_gate.py`.
- Run `scripts/generate_governance_report.py` before capstone demo.
- Maintain human-in-the-loop runbook for high-score fraud blocks.
- Re-train when drift report exceeds configured thresholds (agent week 10).
"""


def section_count(markdown: str) -> int:
    return sum(1 for title in REQUIRED_SECTIONS if f"## {title}" in markdown)


def write_model_card(output: Path | None = None) -> Path:
    output = output or ROOT / "docs" / "model-card.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    content = build_model_card()
    output.write_text(content, encoding="utf-8")
    return output