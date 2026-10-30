# Shared settings of the week-9 lab scripts. Source it: . scripts/lab9/lib.sh
# Override anything with an environment variable, e.g.  LAB9_AIRFLOW_PORT=8090 scripts/lab9/07_portforward.sh
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LAB9_DIR="$ROOT/.lab9"                      # generated files, downloaded binaries, port-forward PIDs
CLUSTER="${LAB9_CLUSTER:-lab9}"
KCTX="kind-$CLUSTER"
IMAGE="${LAB9_IMAGE:-fraud-train:lab9}"

# Ports on your laptop (change if one is taken; 5000 and 8080 are often busy)
MLFLOW_PORT="${LAB9_MLFLOW_PORT:-5001}"
AIRFLOW_PORT="${LAB9_AIRFLOW_PORT:-8082}"
RAY_PORT="${LAB9_RAY_PORT:-8265}"
API_PORT="${LAB9_API_PORT:-8088}"

# Pinned versions (tested together)
KIND_VERSION="${LAB9_KIND_VERSION:-v0.33.0}"
KIND_NODE_IMAGE="${LAB9_KIND_NODE_IMAGE:-kindest/node:v1.37.0}"   # default image of kind v0.33.0 (sha256:a1ed56cfb0e7b93589bdf97c8cd566405a265939e3620fc4f5de89adff580ae5)
KUBECTL_VERSION="${LAB9_KUBECTL_VERSION:-v1.37.1}"
HELM_VERSION="${LAB9_HELM_VERSION:-v3.22.1}"            # chart 1.22.0 documents Helm 3 (>= 3.19); Helm 4.x untested
AIRFLOW_CHART_VERSION="1.22.0"              # ships Airflow 3.2.2
AIRFLOW_IMAGE="apache/airflow:3.2.2"
AIRFLOW_PG_IMAGE="${LAB9_AIRFLOW_PG_IMAGE:-}" # filled by 00_preflight from the chart
KUBERAY_VERSION="1.7.1"
KUBERAY_IMAGE="quay.io/kuberay/operator:v1.7.1"
MLFLOW_IMAGE="ghcr.io/mlflow/mlflow:v3.15.2"
METRICS_SERVER_IMAGE="registry.k8s.io/metrics-server/metrics-server:v0.9.0"
METRICS_SERVER_MANIFEST="https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.9.0/components.yaml"
XCOM_SIDECAR_IMAGE="alpine:3.23.4"           # = XCOM_SIDECAR_IMAGE of apache-airflow-providers-cncf-kubernetes 10.17.1 (in apache/airflow:3.2.2)
DAG_ID="fraud_pipeline"

mkdir -p "$LAB9_DIR/bin"
export PATH="$LAB9_DIR/bin:$PATH"
export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"

say()  { printf '\n\033[1;34m== %s\033[0m\n' "$*"; }
note() { printf '\033[0;36m   %s\033[0m\n' "$*"; }
die()  { printf '\033[0;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }
need() { command -v "$1" >/dev/null 2>&1 || die "'$1' not found - run scripts/lab9/00_preflight.sh first"; }
k()    { kubectl --context "$KCTX" "$@"; }
