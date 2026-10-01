# Testing & Validation — Week 15

## ML test pyramid (this project)

| Level | Tests |
|-------|-------|
| Unit | `tests/test_api.py`, `tests/test_model.py` |
| Data contract | `tests/test_data_contract.py`, `validation/data_contract.py` |
| Model slices | `tests/test_model_slices.py` |
| Integration | `tests/test_pipeline_e2e.py` |
| Adversarial | `tests/test_adversarial.py` |
| System | Week 6 CI, week 12 Locust, week 13 security |

## Quick demo

```bash
pip install -r requirements-testing.txt -r requirements.txt
python scripts/bootstrap.py
python scripts/run_data_validation.py
pytest tests/ -v
python scripts/ab_test_harness.py --baseline metrics.json --candidate docs/fl-results.json
```

## Data contract

`validation/data_contract.py` implements >=10 Great Expectations-style checks:
- schema, nulls, ranges, class balance, variance

Report: `docs/data-validation-report.json`

## Traceability

See `docs/traceability.md` — maps NFR IDs to automated tests and CI jobs.

## CI

`.github/workflows/ml-pipeline.yml` includes `data-validation` job before model gate.

## NFR (v1.14)

| ID | Requirement |
|----|-------------|
| NFR-58 | >= 10 data expectations |
| NFR-59 | E2E pipeline test passes |
| NFR-60 | accuracy >= 0.95 regression gate |
| NFR-61 | critical NFR traceability coverage |