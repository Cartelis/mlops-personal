#!/usr/bin/env bash
# Step 4: Airflow 3 in namespace airflow with the official Helm chart and k8s/lab9/values-airflow.yaml.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"; need kubectl; need helm
say "4.1 Volumes and RBAC the pipeline needs"
k apply -f k8s/lab9/airflow-dags-volume.yaml -f k8s/lab9/pvc-work.yaml -f k8s/lab9/rbac-deploy.yaml
say "4.2 helm upgrade --install airflow apache-airflow/airflow --version $AIRFLOW_CHART_VERSION  (3-5 minutes)"
helm repo add apache-airflow https://airflow.apache.org >/dev/null 2>&1 || true
helm upgrade --install airflow apache-airflow/airflow --version "$AIRFLOW_CHART_VERSION" \
  --namespace airflow -f k8s/lab9/values-airflow.yaml --timeout 15m --wait
say "4.3 Components"
k -n airflow get pods
say "Airflow is up. Next: scripts/lab9/05_ray.sh   (UI: scripts/lab9/07_portforward.sh, user admin / admin)"
