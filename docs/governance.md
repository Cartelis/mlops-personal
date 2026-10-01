# AI Governance — Fraud Detection API (Week 16)

## System overview

Real-time fraud scoring API for card transactions. Semester reference project
integrating MLOps CI/CD, observability, security, edge/FL, and testing gates.

## Risk classification (EU AI Act)

| Field | Value |
|-------|-------|
| **System** | Automated fraud scoring API |
| **Context** | Financial services / payment fraud |
| **Risk tier** | **High-risk** (creditworthiness-adjacent decision support) |
| **Justification** | Automated scoring influences transaction routing; errors harm consumers and merchants |

## Intended use

- **In scope:** Flag suspicious card transactions for analyst review; support payment routing rules.
- **Out of scope:** Sole automated account closure; employment or credit underwriting without human review.

## Mitigations

| Risk | Mitigation | Evidence |
|------|------------|----------|
| Discriminatory outcomes | Slice fairness tests, TPR gap monitoring | `tests/test_model_slices.py`, NFR-05 |
| Data drift | Evidently reports + self-healing agent | `agents/mlops_agent.py`, NFR-38 |
| Security / extraction | Watermark, network policy, Trivy scan | `docs/security-audit.json`, NFR-50 |
| Opaque decisions | Model card, inference audit log | `docs/model-card.md`, NFR-52 |
| Unauthorized deploy | CI gates, model registry approval | `.github/workflows/ml-pipeline.yml` |

## Human oversight

- High-confidence fraud blocks require analyst review per `docs/runbook.md`.
- Agent-initiated retrain/deploy requires explicit `--approve` (week 10).
- Production promotion uses GitOps + CI model gate (week 6).

## Data governance

- PII rejected at API (`tests/test_api.py::test_predict_rejects_pii`).
- Training data contract: >= 10 expectations (`validation/data_contract.py`).
- FL clients keep raw data local (week 14).

## Residual risk

- Synthetic training data may not represent production fraud patterns.
- Fairness proxy uses tabular slices only; geographic bias may need additional features.
- Edge quantized model may slightly reduce accuracy vs cloud model.

## Audit trail

```
Git commit → CI artefacts → MLflow run → K8s manifest → inference audit log
```

## Owners

| Role | Owner |
|------|-------|
| Model Owner | mlops-team |
| Platform | course infra |
| Security / Compliance | team + CI security workflow |

## Capstone evidence bundle

1. `docs/model-card.md`
2. `docs/traceability.md`
3. `docs/governance-report.json`
4. `docs/capstone-checklist.md`
5. `pytest tests/ -v` (green)