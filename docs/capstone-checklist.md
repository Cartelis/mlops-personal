# Capstone Readiness Checklist — Week 16

**Critical items:** 12/12 green

| Item | Path | Status |
|------|------|--------|
| Trained model artefact | `models/model.pkl` | green |
| Evaluation metrics | `metrics.json` | green |
| Living requirements | `docs/requirements.md` | green |
| NFR traceability | `docs/traceability.md` | green |
| Model card | `docs/model-card.md` | green |
| EU AI Act assessment | `docs/governance.md` | green |
| CI workflow | `.github/workflows/ml-pipeline.yml` | green |
| Automated tests | `tests/test_pipeline_e2e.py` | green |
| Data validation | `validation/data_contract.py` | green |
| Gatekeeper policies | `security/policies` | green |
| Monitoring config | `monitoring/prometheus.yml` | green |
| API serving | `src/serve.py` | green |

## Pre-demo commands

```bash
python scripts/bootstrap.py
pytest tests/ -v
python scripts/generate_governance_report.py
python -m uvicorn src.serve:app --port 8080
```
