#!/usr/bin/env bash
# GPU extension, step 11: build the LLM image (PyTorch + Ray + W&B + the book's package), ~7 GB.
set -euo pipefail
. "$(dirname "$0")/../lib.sh"; . "$(dirname "$0")/lib_gpu.sh"
cd "$ROOT"
say "11.1 docker build -f docker/Dockerfile.llm -t $LLM_IMAGE"
docker build -f docker/Dockerfile.llm -t "$LLM_IMAGE" .
docker run --rm "$LLM_IMAGE"
docker image inspect "$LLM_IMAGE" --format '   size: {{.Size}} bytes'
