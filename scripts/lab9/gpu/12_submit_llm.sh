#!/usr/bin/env bash
# GPU extension, step 12: the fine-tuning as a RayJob. KubeRay creates the Ray cluster (CPU head + GPU worker),
# submits ray_train_llm.py, streams the log, and tears the cluster down afterwards.
#   scripts/lab9/gpu/12_submit_llm.sh            # run (W&B online if WANDB_API_KEY is set, else offline)
#   scripts/lab9/gpu/12_submit_llm.sh dashboard  # port-forward the Ray dashboard while the job runs
set -euo pipefail
. "$(dirname "$0")/../lib.sh"; . "$(dirname "$0")/lib_gpu.sh"
cd "$ROOT"
if [ "${1:-}" = "dashboard" ]; then
  head="$(kg -n ray-gpu get svc -l ray.io/node-type=head -o name | head -1)"
  [ -n "$head" ] || die "no Ray head service yet"
  say "Ray dashboard at http://localhost:$RAY_PORT (Ctrl-C to stop)"; kg -n ray-gpu port-forward "$head" "$RAY_PORT:8265"; exit 0
fi
say "12.1 W&B"
if [ -n "${WANDB_API_KEY:-}" ]; then
  kg -n ray-gpu create secret generic wandb --from-literal=WANDB_API_KEY="$WANDB_API_KEY" --from-literal=WANDB_MODE=online \
    --dry-run=client -o yaml | kg apply -f - >/dev/null
  note "Secret 'wandb' set from WANDB_API_KEY - the run will appear in your W&B project"
else
  note "WANDB_API_KEY not set - W&B runs offline inside the pod (export it and re-run to log online)"
fi
say "12.2 kubectl apply -f k8s/lab9/gpu/rayjob-llm.yaml"
kg delete rayjob qwen3-distill -n ray-gpu --ignore-not-found >/dev/null
kg apply -f k8s/lab9/gpu/rayjob-llm.yaml
say "12.3 Waiting for the Ray cluster (head + GPU worker) and the job"
for i in $(seq 1 120); do
  st="$(kg -n ray-gpu get rayjob qwen3-distill -o jsonpath='{.status.jobDeploymentStatus}' 2>/dev/null || true)"
  [ "$st" = "Running" ] || [ "$st" = "Complete" ] || [ "$st" = "Failed" ] && break; sleep 5
done
kg -n ray-gpu get pods
submitter="$(kg -n ray-gpu get pods -l job-name=qwen3-distill -o name | head -1)"
[ -n "$submitter" ] && kg -n ray-gpu logs -f "$submitter" || true
kg -n ray-gpu get rayjob qwen3-distill -o jsonpath='{"   job status: "}{.status.jobStatus}{"  deployment: "}{.status.jobDeploymentStatus}{"\n"}'
