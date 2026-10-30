"""A 70-line client for the Airflow 3 REST API - what the lab scripts (and the UI buttons) really do.

  python scripts/lab9/airflow_api.py trigger fraud_pipeline '{"max_depth": 1}'
  python scripts/lab9/airflow_api.py watch   fraud_pipeline [run_id]     # task state changes until the run ends
  python scripts/lab9/airflow_api.py approve fraud_pipeline [run_id]     # answer the ApprovalOperator
  python scripts/lab9/airflow_api.py status  fraud_pipeline              # last five runs
  python scripts/lab9/airflow_api.py logs    fraud_pipeline <run_id> <task_id>
  python scripts/lab9/airflow_api.py clear   fraud_pipeline <task_id> [run_id] # re-run one task of a finished run

Only the standard library; the API base URL comes from AIRFLOW_API (default http://localhost:8082),
credentials from AIRFLOW_USER / AIRFLOW_PASSWORD (default admin / admin).
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.error
import urllib.request

API = os.environ.get("AIRFLOW_API", "http://localhost:8082").rstrip("/")
USER, PASSWORD = os.environ.get("AIRFLOW_USER", "admin"), os.environ.get("AIRFLOW_PASSWORD", "admin")
TERMINAL = {"success", "failed"}


def call(method: str, path: str, body: dict | None = None, token: str | None = None, raw: bool = False):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = resp.read()
    return payload.decode() if raw else json.loads(payload)


def login() -> str:
    try:
        return call("POST", "/auth/token", {"username": USER, "password": PASSWORD})["access_token"]
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"cannot log in at {API} ({exc}) - is scripts/lab9/07_portforward.sh running?")


def quote(run_id: str) -> str:
    return urllib.parse.quote(run_id, safe="")


def last_run(token: str, dag: str) -> str:
    runs = call("GET", f"/api/v2/dags/{dag}/dagRuns?order_by=-run_after&limit=1", token=token)["dag_runs"]
    if not runs:
        sys.exit(f"no runs of {dag} yet")
    return runs[0]["dag_run_id"]


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, dag, rest = sys.argv[1], sys.argv[2], sys.argv[3:]
    token = login()

    if cmd == "trigger":
        conf = json.loads(rest[0]) if rest else {}
        r = call("POST", f"/api/v2/dags/{dag}/dagRuns", {"logical_date": None, "conf": conf}, token)
        print(f"   run id: {r['dag_run_id']}  state: {r['state']}  conf: {r.get('conf')}")

    elif cmd == "status":
        for r in call("GET", f"/api/v2/dags/{dag}/dagRuns?order_by=-run_after&limit=5", token=token)["dag_runs"]:
            print(f"   {r['dag_run_id']:45s} {r['state']:10s} conf={r.get('conf')}")

    elif cmd == "approve":
        run = rest[0] if rest else last_run(token, dag)
        try:
            r = call("PATCH", f"/api/v2/dags/{dag}/dagRuns/{quote(run)}/taskInstances/approve/-1/hitlDetails",
                     {"chosen_options": ["Approve"]}, token)
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 409):      # the approve task is not waiting (yet, or any more)
                ti = call("GET", f"/api/v2/dags/{dag}/dagRuns/{quote(run)}/taskInstances/approve", token=token)
                sys.exit(f"   nothing to approve: task 'approve' of {run} is {ti['state']} "
                         f"(it must be 'deferred' - run '08_trigger_run.sh watch' and approve when it says so)")
            raise
        print(f"   approved {dag} / {run}: by {r['responded_by']['name']} at {r['responded_at']}")

    elif cmd == "clear":                                   # re-run one task of a finished run (the idempotency drill)
        task = rest[0]
        run = rest[1] if len(rest) > 1 else last_run(token, dag)
        r = call("POST", f"/api/v2/dags/{dag}/clearTaskInstances",
                 {"dry_run": False, "task_ids": [task], "dag_run_id": run, "include_downstream": False,
                  "include_upstream": False, "include_future": False, "include_past": False,
                  "only_failed": False, "reset_dag_runs": True}, token)
        print(f"   cleared {len(r.get('task_instances', []))} task instance(s) of {dag} / {run}: {task} will run again")

    elif cmd == "logs":
        run, task = rest[0], rest[1]
        attempt = rest[2] if len(rest) > 2 else "1"
        log = call("GET", f"/api/v2/dags/{dag}/dagRuns/{quote(run)}/taskInstances/{task}/logs/{attempt}?full_content=true",
                   token=token)
        for entry in log.get("content", []):                 # structured log: one JSON object per line
            if isinstance(entry, dict) and "event" in entry:
                stamp = (entry.get("timestamp") or "")[11:19]
                print(f"{stamp} {entry['event']}")
            else:
                print(entry)

    elif cmd == "watch":
        run = rest[0] if rest else last_run(token, dag)
        print(f"   watching {dag} / {run}  (when 'approve' is deferred: scripts/lab9/08_trigger_run.sh approve)")
        seen: dict[str, str] = {}
        started = time.time()
        while True:
            tis = call("GET", f"/api/v2/dags/{dag}/dagRuns/{quote(run)}/taskInstances?limit=100", token=token)["task_instances"]
            for t in sorted(tis, key=lambda t: (t["start_date"] or "9", t["task_id"])):
                if seen.get(t["task_id"]) != t["state"]:
                    seen[t["task_id"]] = t["state"]
                    print(f"   {time.strftime('%H:%M:%S')}  {t['task_id']:12s} {t['state']}", flush=True)
            state = call("GET", f"/api/v2/dags/{dag}/dagRuns/{quote(run)}", token=token)["state"]
            if state in TERMINAL:
                print(f"   {time.strftime('%H:%M:%S')}  run {state} after {time.time() - started:.0f} s of watching")
                sys.exit(0 if state == "success" else 1)
            time.sleep(5)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
