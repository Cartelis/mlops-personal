#!/usr/bin/env bash
# Step 7: port-forwards from your laptop to the four web UIs/APIs. Each one restarts itself when its pod is
# replaced (the deploy step restarts fraud-api, so a plain port-forward would die there). 'stop' ends them.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"; need kubectl
pidfile="$LAB9_DIR/portforward.pids"
stop_all() {
  if [ -f "$pidfile" ]; then xargs -r kill < "$pidfile" 2>/dev/null || true; rm -f "$pidfile"; fi
  pkill -f "kubectl --context $KCTX .* port-forward" 2>/dev/null || true
}
stop_all
[ "${1:-}" = "stop" ] && { say "port-forwards stopped"; exit 0; }
say "7.1 Starting port-forwards (logs in $LAB9_DIR/portforward.log)"
: > "$LAB9_DIR/portforward.log"
pf() {  # namespace service local:remote - a loop that re-connects after the target pod changes
  ( while true; do k -n "$1" port-forward "$2" "$3" >> "$LAB9_DIR/portforward.log" 2>&1 || true; sleep 2; done ) \
    > /dev/null 2>&1 < /dev/null &
  echo $! >> "$pidfile"
}
pf mlops   svc/mlflow              "$MLFLOW_PORT:5000"
pf airflow svc/airflow-api-server  "$AIRFLOW_PORT:8080"
pf airflow svc/fraud-ray-head-svc  "$RAY_PORT:8265"
pf mlops   svc/fraud-api           "$API_PORT:80"
sleep 3
cat <<TXT
   MLflow     http://localhost:$MLFLOW_PORT
   Airflow    http://localhost:$AIRFLOW_PORT      (admin / admin)
   Ray        http://localhost:$RAY_PORT
   fraud-api  http://localhost:$API_PORT/health   (503 until a champion is promoted)
TXT
say "Port-forwards running in the background. Next: scripts/lab9/08_trigger_run.sh smoke"
