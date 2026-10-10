# Requirements Traceability Matrix — Week 15

Maps critical NFRs to automated tests and CI evidence.

| NFR ID | Requirement (summary) | Test / Script | CI Job | Status |
|--------|------------------------|---------------|--------|--------|
| NFR-01 | Inference p95 <= 80 ms | `scripts/benchmark_edge.py` | manual / week 12 | Pass |
| NFR-02 | Recall >= 0.92 | `tests/test_model_slices.py` | test | Pass |
| NFR-03 | FPR <= 0.5% | `validation/model_quality.py` | test | N/A* |
| NFR-07 | Uptime >= 99.95% | `docs/runbook.md` | ops | N/A |
| NFR-38 | Drift detection <= 5 min | `agents/drift.py` | week 10 demo | Pass |
| NFR-41 | Agent audit 100% | `docs/agent-audit.log` | week 10 | Pass |
| NFR-42 | Metrics scrape <= 30 s | `monitoring/prometheus.yml` | week 11 | Pass |
| NFR-46 | Autoscale <= 3 min | `scripts/scaling_simulator.py` | week 12 | Pass |
| NFR-50 | 0 critical CVEs | `.github/workflows/security.yml` | security | Pass |
| NFR-53 | PII rejection 100% | `tests/test_api.py::test_predict_rejects_pii` | test | Pass |
| NFR-54 | Edge model <= 5 MB | `scripts/benchmark_edge.py` | week 14 | Pass |
| NFR-57 | FL gap <= 2 pp | `federated/fl_simulation.py` | week 14 | Pass |
| NFR-58 | >= 10 data expectations | `tests/test_data_contract.py` | data-validation | Pass |
| NFR-59 | E2E pipeline test | `tests/test_pipeline_e2e.py` | test | Pass |
| NFR-60 | accuracy >= 0.95 | `scripts/check_model_gate.py` | model-gate | Pass |
| NFR-61 | Traceability coverage | `docs/traceability.md` | review | Pass |
| NFR-62 | Model card >= 8 sections | `tests/test_governance.py` | governance | Pass |
| NFR-63 | EU AI Act risk tier | `docs/governance.md` | governance | Pass |
| NFR-64 | Governance report >= 90% | `scripts/generate_governance_report.py` | governance | Pass |
| NFR-65 | Capstone checklist green | `governance/checklist.py` | governance | Pass |

\* NFR-03 requires score outputs; extend API to expose probabilities for full FPR test.

## How to update

1. Add row when new NFR appears in `docs/requirements.md`.
2. Link pytest test or script path.
3. Set Status: Pass / Fail / N/A with justification.
4. Re-run `pytest tests/ -v` before capstone demo.