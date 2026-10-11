# Model Card — Fraud Detection Classifier

## Model Details

- **Model name:** fraud-detection-rf
- **Version:** 1.0.0
- **Owner:** mlops-team
- **Architecture:** scikit-learn RandomForest (tabular)
- **Generated:** 2026-10-10 10:09 UTC

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
| Accuracy | 0.925 | >= 0.95 (NFR-60) |
| F1 | 0.9250093752343809 | — |
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
