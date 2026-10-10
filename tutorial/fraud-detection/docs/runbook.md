# Incident Runbook — Fraud Detection API

## 1. FraudApiHighLatencyP95

**Symptom:** Grafana panel / Prometheus alert `FraudApiHighLatencyP95` firing.

**Diagnosis:**
```promql
histogram_quantile(0.95, sum(rate(fraud_api_request_duration_seconds_bucket[5m])) by (le))
```
```bash
# Structured logs (capture uvicorn stdout)
python scripts/query_logs.py --slow-ms 80 --last 500
```
```logql
{app="mlops-fraud-api"} | json | duration_ms > 80
```

**Mitigation:**
1. Check pod CPU/memory: `kubectl top pods -n mlops`
2. Check concurrent load; scale replicas if infra-bound
3. If correlated with drift (see scenario 3), trigger self-healing agent

**Escalation:** p95 > 200 ms for 30 min after scale attempt.

---

## 2. FraudApiHighErrorRate

**Symptom:** 5xx rate above 0.1%.

**Diagnosis:**
```promql
sum(rate(fraud_api_requests_total{status=~"5.."}[5m])) / sum(rate(fraud_api_requests_total[5m]))
```
```bash
python scripts/query_logs.py | jq '.errors'
```

**Mitigation:**
1. Check model file mount: `MODEL_PATH`, `models/model.pkl`
2. Rollback via ArgoCD / previous image tag
3. Verify `/health` on all pods

**Escalation:** Error rate > 1% for 10 min.

---

## 3. FraudDataDrift (PSI > 0.25)

**Symptom:** `fraud_drift_psi` gauge or Evidently report shows drift.

**Diagnosis:**
```bash
python -m observability.evidently_report --output docs/drift-report.json
cat docs/drift-report.json
python scripts/aiops_correlate.py --drift-report docs/drift-report.json
```

**Mitigation:**
1. Confirm drift is real (not bad batch ingest)
2. Trigger self-healing agent (week 10):
   ```bash
   python scripts/simulate_drift.py   # lab only
   python -m agents.mlops_agent --incident-id DR-<DATE>
   touch approvals/production.flag
   python -m agents.mlops_agent --incident-id DR-<DATE> --approve
   ```
3. Post-deploy: verify accuracy in MLflow and latency SLO

**Escalation:** Drift + accuracy drop confirmed; agent blocked or gate failed.