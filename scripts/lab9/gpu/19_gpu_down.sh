#!/usr/bin/env bash
set -euo pipefail
. "$(dirname "$0")/../lib.sh"; . "$(dirname "$0")/lib_gpu.sh"
say "Deleting minikube profile $GPU_PROFILE"
minikube delete -p "$GPU_PROFILE" || true
