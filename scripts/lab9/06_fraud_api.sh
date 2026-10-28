#!/usr/bin/env bash
# Step 6: the model service (namespace mlops). It stays not-ready until the pipeline promotes a champion.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"; need kubectl
say "6.1 kubectl apply -f k8s/lab9/fraud-api.yaml"
k apply -f k8s/lab9/fraud-api.yaml
sleep 5
k -n mlops get deploy,pods -l app=fraud-api
note "READY 0/1 is expected now: no champion model exists yet. Next: scripts/lab9/07_portforward.sh"
