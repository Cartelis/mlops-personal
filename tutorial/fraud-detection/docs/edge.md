# Edge MLOps — Week 14

## Pipeline

```
models/model.pkl -> ONNX -> INT8 quantize -> model.edge.onnx
    -> Dockerfile.edge -> deploy/edge (K3s/MicroK8s)
```

## Quick demo

```bash
pip install -r requirements-edge-fl.txt
python scripts/bootstrap.py
python scripts/export_onnx.py
python scripts/optimize_edge_model.py
python scripts/benchmark_edge.py --output docs/edge-benchmark.json

docker build -f docker/Dockerfile.edge -t mlops-edge:local .
docker run --rm -p 8081:8080 mlops-edge:local
curl -s localhost:8081/health
```

## Kubernetes (edge)

```bash
kubectl apply -f deploy/edge/deployment-edge.yaml
```

Tuned for single-node K3s/MicroK8s: 128Mi RAM request, 1 replica.

## Targets (NFR-54, NFR-55)

| Metric | Target |
|--------|--------|
| Model size | <= 5 MB |
| Local inference p95 | <= 50 ms |

Check `docs/edge-benchmark.json` after `benchmark_edge.py`.

## Tiered inference

1. **Edge** — `model.edge.onnx` on POS/IoT for low-latency scoring
2. **Cloud** — full `serve.py` API for explainability / heavy features
3. **FL round** — update global model without centralizing raw data