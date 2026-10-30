#!/usr/bin/env bash
# Step 0 (at home, before the lab): tools, images and resources. Safe to re-run.
#   - checks docker, installs kind/kubectl/helm into .lab9/bin if they are missing
#   - pulls every public image the lab needs (~2.5 GB) so the lab itself needs no download
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"

say "0.1 Docker"
docker version --format 'client {{.Client.Version}} / server {{.Server.Version}}' || die "Docker is not running"
note "Docker Desktop (macOS/Windows): give the VM at least 8 GB of memory (Settings > Resources)."

say "0.2 Tools (kind, kubectl, helm) - downloaded into .lab9/bin if missing or another version"
os="$(uname -s | tr '[:upper:]' '[:lower:]')"; arch="$(uname -m)"
case "$arch" in x86_64) arch=amd64;; aarch64|arm64) arch=arm64;; esac
# An older kind (e.g. v0.20 from an earlier course) cannot start the kindest/node:v1.37 image, and the chart
# needs helm >= 3.19 - so the version is checked, not only presence. .lab9/bin comes first in PATH (lib.sh).
if ! kind version 2>/dev/null | grep -qF "$KIND_VERSION "; then
  curl -fsSLo "$LAB9_DIR/bin/kind" "https://kind.sigs.k8s.io/dl/$KIND_VERSION/kind-$os-$arch" && chmod +x "$LAB9_DIR/bin/kind"
fi
if ! kubectl version --client 2>/dev/null | grep -qF "$KUBECTL_VERSION"; then
  curl -fsSLo "$LAB9_DIR/bin/kubectl" "https://dl.k8s.io/release/$KUBECTL_VERSION/bin/$os/$arch/kubectl" && chmod +x "$LAB9_DIR/bin/kubectl"
fi
if ! helm version --short 2>/dev/null | grep -qF "$HELM_VERSION+"; then
  curl -fsSL "https://get.helm.sh/helm-$HELM_VERSION-$os-$arch.tar.gz" | tar -xzO "$os-$arch/helm" > "$LAB9_DIR/bin/helm" && chmod +x "$LAB9_DIR/bin/helm"
fi
kind version; kubectl version --client; helm version --short

say "0.3 Helm repositories"
helm repo add apache-airflow https://airflow.apache.org >/dev/null 2>&1 || true
helm repo add kuberay https://ray-project.github.io/kuberay-helm/ >/dev/null 2>&1 || true
helm repo update >/dev/null
pg_image="$(helm show values apache-airflow/airflow --version "$AIRFLOW_CHART_VERSION" | python3 -c '
import sys, re
txt = sys.stdin.read()
# chart 1.22.0 has no registry line and quotes the tag:  image:  repository: bitnamilegacy/postgresql  tag: "16.1.0-debian-11-r15"
q = r"[\"\x27]?"   # optional quote around a value
m = re.search(r"^postgresql:\n(?:.*\n)*?\s+image:\n(?:\s+registry:\s*" + q + r"(\S+?)" + q + r"\n)?\s+repository:\s*" + q + r"(\S+?)" + q + r"\n\s+tag:\s*" + q + r"(\S+?)" + q + r"\n", txt, re.M)
print((m.group(1) + "/" if m.group(1) else "") + m.group(2) + ":" + m.group(3) if m else "")
')"
note "PostgreSQL image used by the Airflow chart: ${pg_image:-unknown}"
echo "$pg_image" > "$LAB9_DIR/airflow-pg-image.txt"

say "0.4 Public images (pulled now so the lab needs no network)"
for img in "$KIND_NODE_IMAGE" "$AIRFLOW_IMAGE" "$KUBERAY_IMAGE" "$MLFLOW_IMAGE" "$XCOM_SIDECAR_IMAGE" "$METRICS_SERVER_IMAGE" ${pg_image:+"$pg_image"}; do
  docker image inspect "$img" >/dev/null 2>&1 && note "present: $img" || docker pull "$img"
done

say "0.5 Resources and ports"
if [ -r /proc/sys/fs/inotify/max_user_instances ]; then
  inst="$(cat /proc/sys/fs/inotify/max_user_instances)"
  if [ "$inst" -lt 512 ]; then
    note "fs.inotify.max_user_instances=$inst (Linux default 128) - kind/minikube hit 'too many open files' with it;"
    note "   fix once:  sudo sysctl -w fs.inotify.max_user_instances=8192 fs.inotify.max_user_watches=1048576"
  else note "inotify limits fine (max_user_instances=$inst)"; fi
fi
if command -v free >/dev/null; then free -g | awk 'NR==2{printf "   RAM: %s GB total, %s GB available (the lab needs ~6 GB free)\n",$2,$7}'; fi
for p in "$MLFLOW_PORT" "$AIRFLOW_PORT" "$RAY_PORT" "$API_PORT"; do
  if (command -v ss >/dev/null && ss -ltn | grep -q ":$p ") || (command -v lsof >/dev/null && lsof -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1); then
    note "port $p is in use - set LAB9_*_PORT to another value (see scripts/lab9/lib.sh)"
  else note "port $p free"; fi
done
say "Preflight done. Next: scripts/lab9/01_build_image.sh"
