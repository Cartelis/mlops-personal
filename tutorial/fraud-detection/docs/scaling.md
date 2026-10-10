# Scaling & Cost Engineering — Week 12

## Architecture

```
Locust load test -> fraud API (instrumented week 11)
    -> Prometheus RPS / CPU metrics
    -> HPA (CPU/memory) OR KEDA (Prometheus trigger)
    -> Node pool: spot (GKE) / Karpenter (AWS)
TCO calculator -> cost-optimization-report.md
```

## Local demo

```bash
pip install -r requirements-scaling.txt
python -m uvicorn src.serve:app --port 8080 &

python scripts/run_load_test.py --users 50 --spawn-rate 10 --run-time 1m
python scripts/scaling_simulator.py --rps 800
python scripts/tco_calculator.py --baseline
python scripts/tco_calculator.py --replicas 32 --spot --rightsizing
```

## Kubernetes

```bash
kubectl apply -f k8s/hpa-fraud-api.yaml
kubectl apply -f k8s/keda-scaledobject.yaml   # requires KEDA + Prometheus

# Watch scaling during load test
kubectl get hpa -n mlops -w
```

## Spot / preemptible

| Platform | Config |
|----------|--------|
| AWS | `deploy/scaling/karpenter-nodepool.yaml` |
| GCP | `infra/modules/gke_spot/` Terraform module |

## Targets (NFR-46–NFR-49)

| Metric | Target |
|--------|--------|
| Autoscale response | <= 3 min |
| Max replicas | 50 |
| Spot cost savings | >= 60% vs on-demand baseline |
| Uptime during scale | >= 99.9% |

## SLO validation during load test

1. Run Locust with 50 users
2. Check `docs/locust-stats_stats.csv` for p95 latency
3. Compare against NFR-01 (p95 <= 80 ms)
4. Document in `docs/cost-optimization-report.md`