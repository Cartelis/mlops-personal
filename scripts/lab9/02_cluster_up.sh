#!/usr/bin/env bash
# Step 2: the lab cluster (kind) with your DAG folder mounted into the node, plus the images it needs.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"
need kind; need kubectl

say "2.1 kind cluster '$CLUSTER' ($KIND_NODE_IMAGE)"
dags_dir="$ROOT/pipeline/dags"
chmod -R a+rX "$dags_dir"                    # Airflow runs as uid 50000 inside the node: files must be world-readable
sed "s|__DAGS_DIR__|$dags_dir|" k8s/lab9/kind-cluster.yaml > "$LAB9_DIR/kind-cluster.yaml"
if kind get clusters 2>/dev/null | grep -qx "$CLUSTER"; then
  note "cluster exists - keeping it (delete with scripts/lab9/99_down.sh)"
else
  kind create cluster --config "$LAB9_DIR/kind-cluster.yaml" --image "$KIND_NODE_IMAGE" --wait 120s
fi
k apply -f k8s/lab9/namespaces.yaml
# kind's documented "too many open files" issue: the kubelet streams pod logs with inotify, and Linux
# defaults (128 instances per user) are shared by every root process on the host, so Airflow's log
# follower hangs. The node container is privileged, so the limit can be raised from inside it.
docker exec "$CLUSTER-control-plane" sysctl -q -w fs.inotify.max_user_instances=8192 fs.inotify.max_user_watches=1048576 >/dev/null 2>&1 \
  && note "inotify limits raised (max_user_instances=8192)" || note "could not raise inotify limits (not Linux?) - see the troubleshooting table if tasks hang"

say "2.2 Loading images into the node (the node has its own image store, separate from Docker's)"
pg_image="$(cat "$LAB9_DIR/airflow-pg-image.txt" 2>/dev/null || true)"
arch="$(uname -m)"; case "$arch" in x86_64) arch=amd64;; aarch64|arm64) arch=arm64;; esac
load_image() {
  # 'kind load docker-image' fails for pulled multi-arch images when Docker uses the containerd image
  # store (default in recent Docker Desktop / Docker 29: "ctr: content digest ...: not found").
  # Fallback: export only our platform and load the archive.
  if ! kind load docker-image --name "$CLUSTER" "$1" 2>"$LAB9_DIR/kind-load.err"; then
    note "kind load docker-image failed ($(tail -1 "$LAB9_DIR/kind-load.err" | cut -c1-80)) - using docker save --platform"
    docker save --platform "linux/$arch" -o "$LAB9_DIR/image.tar" "$1"
    kind load image-archive --name "$CLUSTER" "$LAB9_DIR/image.tar"
    rm -f "$LAB9_DIR/image.tar"
  fi
}
for img in "$IMAGE" "$AIRFLOW_IMAGE" "$KUBERAY_IMAGE" "$MLFLOW_IMAGE" "$XCOM_SIDECAR_IMAGE" "$METRICS_SERVER_IMAGE" ${pg_image:+"$pg_image"}; do
  note "kind load $img"
  load_image "$img"
done

say "2.3 metrics-server, so that 'kubectl top pods -A' shows what each component really uses"
k apply -f "$METRICS_SERVER_MANIFEST" >/dev/null
k -n kube-system patch deployment metrics-server --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]' >/dev/null 2>&1 || true
k -n kube-system rollout status deployment/metrics-server --timeout=120s >/dev/null || note "metrics-server not ready yet (fine, kubectl top works a minute later)"

say "2.4 Cluster state"
k get nodes
k get ns mlops airflow
say "Cluster up. Next: scripts/lab9/03_mlflow.sh"
