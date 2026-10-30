#!/usr/bin/env bash
# Step 5: the KubeRay operator (namespace kuberay) and a small RayCluster next to the pipeline pods.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"; need kubectl; need helm
say "5.1 KubeRay operator $KUBERAY_VERSION"
helm repo add kuberay https://ray-project.github.io/kuberay-helm/ >/dev/null 2>&1 || true
helm upgrade --install kuberay-operator kuberay/kuberay-operator --version "$KUBERAY_VERSION" \
  --namespace kuberay --create-namespace --wait --timeout 5m
say "5.2 RayCluster fraud-ray (k8s/lab9/raycluster.yaml)"
k apply -f k8s/lab9/raycluster.yaml
for i in $(seq 1 60); do
  ready="$(k -n airflow get raycluster fraud-ray -o jsonpath='{.status.state}' 2>/dev/null || true)"
  [ "$ready" = "ready" ] && break; sleep 5
done
k -n airflow get raycluster,pods -l ray.io/cluster=fraud-ray
say "Ray is up (dashboard: scripts/lab9/07_portforward.sh). Next: scripts/lab9/06_fraud_api.sh"
