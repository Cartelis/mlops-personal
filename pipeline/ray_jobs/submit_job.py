"""Submit a script to a Ray cluster and wait for it - the bridge between an Airflow task and Ray.

Runs inside a pipeline pod (image fraud-train:lab9), which has the Ray client library; the
computation happens on the Ray cluster behind --address. Exit code = the job's outcome, so the
Airflow task fails when the job fails. The job's log is printed at the end (and as it runs with --follow).

  python pipeline/ray_jobs/submit_job.py --entrypoint "python /work/pipeline/ray_jobs/tune_fraud.py"
"""
from __future__ import annotations

import argparse
import os
import sys
import time

from ray.job_submission import JobStatus, JobSubmissionClient

DONE = {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.STOPPED}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", default=os.environ.get("RAY_ADDRESS", "http://fraud-ray-head-svc.airflow.svc:8265"))
    parser.add_argument("--entrypoint", required=True, help="command run on the Ray head, e.g. 'python /work/....py --flag'")
    parser.add_argument("--env", action="append", default=[], metavar="KEY=VALUE", help="environment variable for the job (repeatable)")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds to wait before giving up")
    parser.add_argument("--follow", action="store_true", help="print the job log while it runs")
    args = parser.parse_args()

    env = {"MLFLOW_TRACKING_URI": os.environ.get("MLFLOW_TRACKING_URI", "")}
    env.update(dict(kv.split("=", 1) for kv in args.env))
    env = {k: v for k, v in env.items() if v}

    client = JobSubmissionClient(args.address)
    job_id = client.submit_job(entrypoint=args.entrypoint, runtime_env={"env_vars": env} if env else None)
    print(f"submitted job {job_id} to {args.address}: {args.entrypoint}", flush=True)

    started = time.time()
    printed = 0
    status = client.get_job_status(job_id)
    while status not in DONE:
        if time.time() - started > args.timeout:
            client.stop_job(job_id)
            sys.exit(f"job {job_id} timed out after {args.timeout}s")
        if args.follow:
            logs = client.get_job_logs(job_id)
            if len(logs) > printed:
                print(logs[printed:], end="", flush=True)
                printed = len(logs)
        time.sleep(5)
        status = client.get_job_status(job_id)

    logs = client.get_job_logs(job_id)
    print(logs[printed:] if args.follow else logs, end="", flush=True)
    print(f"\njob {job_id} finished with status {status} after {time.time() - started:.0f}s", flush=True)
    sys.exit(0 if status == JobStatus.SUCCEEDED else 1)


if __name__ == "__main__":
    main()
