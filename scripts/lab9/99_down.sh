#!/usr/bin/env bash
# Tear down: port-forwards and the kind cluster. Images stay in Docker (remove with 'docker rmi' if you want the space).
set -euo pipefail
. "$(dirname "$0")/lib.sh"
"$ROOT/scripts/lab9/07_portforward.sh" stop >/dev/null 2>&1 || true
say "Deleting kind cluster '$CLUSTER'"
kind delete cluster --name "$CLUSTER" || true
note "kept: Docker images ($IMAGE, $AIRFLOW_IMAGE, ...) and $LAB9_DIR"
