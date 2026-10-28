#!/usr/bin/env bash
# GPU extension, step 0 (no cluster, no GPU needed): the same script on a laptop with two CPU workers -
# shows the sharding (each worker trains on half of the examples) without any GPU. Slow but small.
set -euo pipefail
. "$(dirname "$0")/../lib.sh"; . "$(dirname "$0")/lib_gpu.sh"
cd "$ROOT"
say "0.1 Python environment .venv-llm (torch, ray, wandb, reasoning-from-scratch)"
if [ ! -x .venv-llm/bin/python ]; then
  uv venv .venv-llm && uv pip install --python .venv-llm/bin/python "torch==2.14.0" -r requirements-llm.txt
fi
say "0.2 Two CPU workers, 4 examples, short sequences (~ a few minutes; first run downloads ~1.6 GB into $LLM_CACHE_DIR)"
mkdir -p "$LLM_CACHE_DIR"
WANDB_MODE=offline .venv-llm/bin/python pipeline/ray_jobs/ray_train_llm.py --no-gpu --num-workers 2 \
  --train-size 4 --val-size 2 --max-seq-len 256 --log-every 2 --data-dir "$LLM_CACHE_DIR"
