#!/usr/bin/env bash
# Step 3: MLflow Tracking Server in namespace mlops (Deployment + Service + PVC), as in assignment U1.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"; need kubectl
say "3.1 kubectl apply -f k8s/lab9/mlflow.yaml"
k apply -f k8s/lab9/mlflow.yaml
say "3.2 Waiting for the server"
k -n mlops rollout status deployment/mlflow --timeout=180s
k -n mlops get pods,svc,pvc
say "MLflow is up at http://mlflow.mlops.svc:5000 inside the cluster. Next: scripts/lab9/04_airflow.sh"
