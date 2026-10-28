#!/usr/bin/env bash
# Step 9: the deployed model answers a request - the end of the pipeline seen from the outside.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"
api="http://localhost:$API_PORT"
say "9.1 GET $api/health"
curl -sS "$api/health"; echo
say "9.2 POST $api/predict with one transaction (10 features)"
curl -sS -X POST "$api/predict" -H 'Content-Type: application/json' \
  -d '{"f0": 1.2, "f1": 0.8, "f2": -0.3, "f3": 0.1, "f4": 0.0, "f5": -1.1, "f6": 0.4, "f7": 0.2, "f8": -0.5, "f9": 0.9}'; echo
say "9.3 The same with f0+f1 < 0 (the synthetic label is sign(f0+f1))"
curl -sS -X POST "$api/predict" -H 'Content-Type: application/json' \
  -d '{"f0": -1.2, "f1": -0.8, "f2": -0.3, "f3": 0.1, "f4": 0.0, "f5": -1.1, "f6": 0.4, "f7": 0.2, "f8": -0.5, "f9": 0.9}'; echo
note "which model answered: curl $api/health shows the model URI and version"
