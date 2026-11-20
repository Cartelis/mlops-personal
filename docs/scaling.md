# Scaling & Cost Engineering — Week 12

Lab text: Skyrius 12. All code: `scaling/`.

## Idea

Resource-based scaling (CPU, HPA) works while CPU is the bottleneck. When a request mostly *waits*
(e.g. for a feature store), CPU stays low while latency explodes, and HPA does nothing.
Request-based scaling (requests per second, KEDA) follows the load itself.

| Act | App | Scaler | Expected |
|-----|-----|--------|----------|
| 1 | CPU-bound "model" | HPA (CPU 70 %) | replicas follow load |
| 2 | + feature store (40 ms, 1 connection) | HPA (CPU 70 %) | 1 replica, p95 in seconds, low CPU |
| 3 | same as 2 | KEDA (RPS, threshold 15/replica) | replicas follow RPS, p95 recovers |

## Architecture

```
Locust Job (in cluster) -> Service fraud-api-lite -> pods (scaling/app.py)
    -> Prometheus (ServiceMonitor)  -> KEDA prometheus trigger -> HPA (created by KEDA)
    -> metrics-server               -> HPA (CPU)
```

Exactly one autoscaler per Deployment: KEDA creates its own HPA, so a separate HPA fights it.

## Run (see the lab for prerequisites: metrics-server, kube-prometheus-stack, KEDA)

```bash
uv run scaling/app.py                              # local, Act 1 mode
docker build -t fraud-api-lite:v1 scaling
kubectl apply -f scaling/k8s/namespace.yaml -f scaling/k8s/deployment.yaml \
              -f scaling/k8s/service.yaml -f scaling/k8s/servicemonitor.yaml
kubectl -n scaling-lab create configmap locustfile --from-file=scaling/locustfile.py
kubectl apply -f scaling/k8s/hpa-cpu.yaml                                   # Act 1 and 2
sed 's/__USERS__/300/' scaling/k8s/loadtest.yaml | kubectl apply -f -
kubectl -n scaling-lab set env deployment/fraud-api-lite FEATURE_STORE_MS=40  # Act 2
kubectl delete -f scaling/k8s/hpa-cpu.yaml && kubectl apply -f scaling/k8s/keda-rps.yaml  # Act 3
```

## Cost model (optional part)

```bash
python scripts/tco_calculator.py --baseline
python scripts/tco_calculator.py --replicas 32 --spot --rightsizing                 # same capacity: 72 %
python scripts/tco_calculator.py --mode autoscale --spot --rightsizing              # vs fixed 5 replicas: 55 %
```

Compare the **same capacity and SLO**; prices are model assumptions, not real quotes.

| Platform | Spot config |
|----------|-------------|
| AWS | `deploy/scaling/karpenter-nodepool.yaml` |
| GCP | `infra/modules/gke_spot/` Terraform module |

## Targets (NFR-46–NFR-49)

| Metric | Target |
|--------|--------|
| Autoscale response | <= 3 min to target replicas (Act 3) |
| Max replicas | 10 in the lab cluster, 50 in production (`maxReplicaCount`) |
| Spot cost savings | >= 60 % vs on-demand at the same capacity |
| Uptime during scale | >= 99.9 % (Locust: 0 failures) |
