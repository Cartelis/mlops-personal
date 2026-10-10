#!/usr/bin/env bash
# Deploy week 5 CPU inference manifests to current kubectl context.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/resourcequota.yaml
kubectl apply -f k8s/deployment-cpu.yaml
kubectl apply -f k8s/service-cpu.yaml

kubectl rollout status deployment/mlops-fraud-api -n mlops
echo "Inference ready. Run: kubectl port-forward svc/mlops-fraud-api 8080:80 -n mlops"