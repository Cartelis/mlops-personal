#!/usr/bin/env bash
# Step 8: drive DAG runs through Airflow's REST API (the UI buttons do the same; scripts/lab9/airflow_api.py).
#   scripts/lab9/08_trigger_run.sh smoke                  -> trigger DAG lab9_smoke
#   scripts/lab9/08_trigger_run.sh A | B | C              -> trigger fraud_pipeline with the lab's parameter sets
#   scripts/lab9/08_trigger_run.sh '{"max_depth": 2}'     -> fraud_pipeline with your own parameters
#   scripts/lab9/08_trigger_run.sh watch [dag] [run_id]   -> task state changes until the run ends
#   scripts/lab9/08_trigger_run.sh approve [dag] [run_id] -> answer the waiting ApprovalOperator with "Approve"
#   scripts/lab9/08_trigger_run.sh status [dag]           -> last runs
#   scripts/lab9/08_trigger_run.sh logs <run_id> <task> [try]  -> a task's log
#   scripts/lab9/08_trigger_run.sh clear <task> [run_id]   -> re-run one task of a finished run (idempotency drill)
set -euo pipefail
. "$(dirname "$0")/lib.sh"
cd "$ROOT"
export AIRFLOW_API="http://localhost:$AIRFLOW_PORT"
api() { python3 scripts/lab9/airflow_api.py "$@"; }
case "${1:-}" in
  smoke)   DAG_ID=lab9_smoke; say "Triggering lab9_smoke"; api trigger lab9_smoke '{}';;
  A|a)     say "Run A: defaults (accuracy ~0.97 -> direct path)";          api trigger "$DAG_ID" '{}';;
  B|b)     say "Run B: max_depth=1 (weak model -> tune on Ray -> rescued)"; api trigger "$DAG_ID" '{"max_depth": 1}';;
  C|c)     say "Run C: threshold=0.999 (unreachable -> red run, nothing registered)"; api trigger "$DAG_ID" '{"threshold": 0.999}';;
  watch)   api watch "${2:-$DAG_ID}" ${3:+"$3"}; exit $?;;
  approve) api approve "${2:-$DAG_ID}" ${3:+"$3"}; exit 0;;
  status)  api status "${2:-$DAG_ID}"; exit 0;;
  logs)    dag="$DAG_ID"; api status lab9_smoke 2>/dev/null | grep -qF -- "$2" && dag=lab9_smoke   # run id of a smoke run?
           api logs "$dag" "$2" "$3" ${4:+"$4"}; exit 0;;
  clear)   api clear "$DAG_ID" "$2" ${3:+"$3"}; exit 0;;
  "")      die "usage: $0 smoke | A | B | C | '<json conf>' | watch | approve | status | logs <run_id> <task>";;
  *)       say "Triggering $DAG_ID with conf=$1"; api trigger "$DAG_ID" "$1";;
esac
note "watch it: scripts/lab9/08_trigger_run.sh watch $DAG_ID   |   http://localhost:$AIRFLOW_PORT/dags/$DAG_ID   |   kubectl --context $KCTX -n airflow get pods -w"
