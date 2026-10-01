# Observability Stack — Week 11

## Architecture

```
FastAPI (/metrics + JSON logs)
    -> Prometheus (scrape + alerts)
    -> Grafana (dashboards)
    -> Loki (log aggregation, optional)
Evidently drift report -> docs/drift-report.json
Drift exporter (:9101) -> fraud_drift_psi metric
AIOps correlate -> links to week 10 self-healing agent
```

## Quick demo (local)

```bash
pip install -r requirements-observability.txt
python scripts/bootstrap.py

# Terminal 1: API
python -m uvicorn src.serve:app --port 8080

# Terminal 2: traffic + drift
python scripts/generate_traffic.py --requests 200
python scripts/simulate_drift.py
python -m observability.evidently_report --output docs/drift-report.json
python scripts/export_drift_metrics.py --port 9101 &

# Terminal 3: analysis
curl -s localhost:8080/metrics | grep fraud_api
python scripts/aiops_correlate.py --drift-report docs/drift-report.json
```

## Optional: Prometheus + Grafana + Loki

```bash
docker compose -f monitoring/docker-compose.yml up -d
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3000 (admin/admin)
# Import monitoring/grafana-dashboard.json
```

## Kubernetes

```bash
kubectl apply -f k8s/servicemonitor.yaml
kubectl apply -f k8s/prometheus-rules.yaml
```

Requires Prometheus Operator installed in cluster.

## Key metrics

| Metric | Type | Purpose |
|--------|------|---------|
| `fraud_api_request_duration_seconds` | Histogram | p50/p95 latency SLO |
| `fraud_api_requests_total` | Counter | RPS, error rate |
| `fraud_predictions_total` | Counter | Output distribution |
| `fraud_drift_psi` | Gauge | Data drift alerting |

## SLIs / SLOs

| SLI | SLO | Alert |
|-----|-----|-------|
| p95 latency | <= 80 ms | FraudApiHighLatencyP95 |
| Error rate | < 0.1% | FraudApiHighErrorRate |
| Drift PSI | < 0.25 | FraudDataDrift |