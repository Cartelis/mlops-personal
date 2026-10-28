#!/usr/bin/env bash
# Step 1: build the one image every pipeline step runs from (training pods, Ray, model service).
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"
commit="$(git rev-parse --short=8 HEAD 2>/dev/null || echo unknown)"
say "1.1 docker build -f docker/Dockerfile.train -t $IMAGE  (GIT_COMMIT=$commit)"
docker build -f docker/Dockerfile.train --build-arg "GIT_COMMIT=$commit" -t "$IMAGE" .
say "1.2 Smoke test: the image prints the versions it carries"
docker run --rm "$IMAGE"
docker image inspect "$IMAGE" --format '   size: {{.Size}} bytes'
say "Image ready. Next: scripts/lab9/02_cluster_up.sh"
