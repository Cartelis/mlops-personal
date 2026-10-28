#!/usr/bin/env bash
# GPU extension, step 10: a second local cluster with the GPU passed through (minikube, docker driver,
# --gpus all), the model/dataset cache mounted into the node, and the lab's LLM image loaded.
set -euo pipefail
. "$(dirname "$0")/../lib.sh"; . "$(dirname "$0")/lib_gpu.sh"
cd "$ROOT"
say "10.1 Prerequisites: NVIDIA driver + container toolkit (docker run --gpus all must work)"
docker run --rm --gpus all "$LLM_IMAGE" python -c "import torch; print('   torch sees', torch.cuda.device_count(), 'GPU(s):', torch.cuda.get_device_name(0))" \
  || die "docker cannot use the GPU - install the NVIDIA container toolkit (nvidia-ctk runtime configure) and build the image (scripts/lab9/gpu/11_build_llm_image.sh)"
if ! command -v minikube >/dev/null; then
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"; arch="$(uname -m)"; case "$arch" in x86_64) arch=amd64;; aarch64|arm64) arch=arm64;; esac
  curl -fsSLo "$LAB9_DIR/bin/minikube" "https://github.com/kubernetes/minikube/releases/download/$MINIKUBE_VERSION/minikube-$os-$arch" && chmod +x "$LAB9_DIR/bin/minikube"
fi
minikube version --short
mkdir -p "$LLM_CACHE_DIR"
say "10.2 minikube start -p $GPU_PROFILE --driver=docker --gpus=all  (cache: $LLM_CACHE_DIR -> /mnt/llm-cache)"
minikube start -p "$GPU_PROFILE" --driver=docker --container-runtime=docker --gpus=all \
  --cpus="$GPU_CPUS" --memory="$GPU_MEMORY" \
  --mount --mount-string="$LLM_CACHE_DIR:/mnt/llm-cache"
docker exec "$GPU_PROFILE" sysctl -q -w fs.inotify.max_user_instances=8192 fs.inotify.max_user_watches=1048576 >/dev/null 2>&1 || true
for i in $(seq 1 30); do   # the NVIDIA device plugin registers the GPU some seconds after the node is Ready
  [ -n "$(kg get nodes -o jsonpath='{.items[0].status.allocatable.nvidia\.com/gpu}' 2>/dev/null)" ] && break; sleep 3
done
kg get nodes -o custom-columns='NODE:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu'
say "10.3 Loading $LLM_IMAGE into the node (several GB - a few minutes)"
minikube -p "$GPU_PROFILE" image load "$LLM_IMAGE"
say "10.4 KubeRay operator in the GPU cluster"
helm repo add kuberay https://ray-project.github.io/kuberay-helm/ >/dev/null 2>&1 || true
helm --kube-context "$GPU_KCTX" upgrade --install kuberay-operator kuberay/kuberay-operator --version "$KUBERAY_VERSION" \
  --namespace kuberay --create-namespace --wait --timeout 5m
kg create namespace ray-gpu --dry-run=client -o yaml | kg apply -f -
say "GPU cluster ready. Next: scripts/lab9/gpu/12_submit_llm.sh"
