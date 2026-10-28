"""Ray-only pipeline of the fraud model - the week-9 reference the week-10 agent calls.

A chain of Ray tasks is a DAG and this script really runs the pipeline, on a local Ray instance:
    ingest -> preprocess -> train -> evaluate -> (tune on Ray Tune if below threshold -> evaluate -> gate)
           -> register (@candidate, idempotent) -> human approval -> promote (@champion) -> deploy
What it does NOT have is a control plane: no schedule, no state across restarts, no retry history a
person can inspect, no audit of who approved. The Airflow DAG in pipeline/dags/fraud_dag.py adds that.

  export MLFLOW_TRACKING_URI=http://localhost:5001      # required: where runs, models and aliases go
  python pipeline/ray_pipeline.py --run-id exp-001                 # stops at "pending_approval"
  touch approvals/production.flag                                  # the human says yes (or --approve)
  python pipeline/ray_pipeline.py --run-id exp-001 --approve       # promote + deploy
Writes metrics.json at the project root (read by week 6's gate and week 10's agent).
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import ray

ACCURACY_THRESHOLD = 0.95
ROOT = Path(__file__).resolve().parents[1]
APPROVAL_FILE = ROOT / "approvals/production.flag"       # anchored to the project, not to the cwd
APPROVAL_LOG = ROOT / "approvals/log.md"


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


@ray.remote(num_cpus=1, max_retries=2, retry_exceptions=True)
def ingest_data(raw_path: str = "data/raw/dataset.csv") -> str:
    if not (ROOT / raw_path).exists():
        _run([sys.executable, "src/ingest.py"])
    return raw_path


@ray.remote(num_cpus=1, max_retries=2, retry_exceptions=True)
def preprocess(_raw_path: str) -> dict[str, str]:
    _run([sys.executable, "src/prepare_data.py"])
    return {"train": "data/processed/train.csv", "test": "data/processed/test.csv"}


@ray.remote(num_cpus=1, max_retries=2, retry_exceptions=True)
def train_model(params: dict | None = None) -> str:
    cmd = [sys.executable, "src/train.py"]
    for key in ("n_estimators", "max_depth"):
        if params and key in params:
            cmd += [f"--{key}", str(params[key])]
    _run(cmd)
    return "models/model.pkl"


@ray.remote(num_cpus=1)
def evaluate_model(_model_path: str) -> dict:
    _run([sys.executable, "src/evaluate.py"])
    return json.loads((ROOT / "metrics.json").read_text())


@ray.remote(num_cpus=0)
def tune_hyperparams(run_id: str) -> dict:
    """Ray Tune grid search on the same Ray instance; retrains the best configuration via src/train.py."""
    _run([sys.executable, "pipeline/ray_jobs/tune_fraud.py", "--tag", f"ray_pipeline_run_id={run_id}"])
    return json.loads((ROOT / "models/tune_result.json").read_text())


@ray.remote(num_cpus=0)
def register_model(run_id: str) -> dict:
    """Idempotent: a second call with the same run id finds the version it made before."""
    _run([sys.executable, "scripts/promote_model.py", "register", "--alias", "candidate",
          "--tag", f"ray_pipeline_run_id={run_id}", "--result", "models/register_result.json"])
    return json.loads((ROOT / "models/register_result.json").read_text())


@ray.remote(num_cpus=0)
def check_human_approval(metrics: dict, force: bool = False) -> bool:
    if force or APPROVAL_FILE.exists():
        return True
    print(f"PENDING HUMAN APPROVAL: accuracy={metrics.get('accuracy', 0):.4f}\n"
          f"Create {APPROVAL_FILE.relative_to(ROOT)} or re-run with --approve")
    return False


@ray.remote(num_cpus=0)
def deploy_model(run_id: str) -> str:
    """The alias move IS the deployment for a service that loads models:/fraud-detector@champion;
    the approval is written to approvals/log.md (who, when) - the audit trail week 16 asks for."""
    who, when = getpass.getuser(), datetime.now(timezone.utc).isoformat(timespec="seconds")
    _run([sys.executable, "scripts/promote_model.py", "promote", "--to", "champion",
          "--tag", f"approved_by={who}", "--tag", f"approved_at={when}"])
    APPROVAL_LOG.parent.mkdir(exist_ok=True)
    with APPROVAL_LOG.open("a") as f:
        f.write(f"| {when} | {who} | run {run_id} | promoted @candidate -> @champion |\n")
    return "promoted-champion"


def run_pipeline(run_id: str, approve: bool = False) -> dict:
    if not os.environ.get("MLFLOW_TRACKING_URI"):
        sys.exit("MLFLOW_TRACKING_URI is not set (e.g. http://localhost:5001) - the pipeline needs the tracking server")
    ray.init(ignore_reinit_error=True)
    print(f"Starting Ray pipeline run_id={run_id}")

    raw = ray.get(ingest_data.remote())
    ray.get(preprocess.remote(raw))
    model_path = ray.get(train_model.remote())
    metrics = ray.get(evaluate_model.remote(model_path))
    tuned = None

    if metrics.get("accuracy", 0) < ACCURACY_THRESHOLD:
        print(f"Accuracy {metrics['accuracy']:.4f} < {ACCURACY_THRESHOLD}, tuning on Ray...")
        tuned = ray.get(tune_hyperparams.remote(run_id))
        metrics = ray.get(evaluate_model.remote("models/model.pkl"))
        if metrics.get("accuracy", 0) < ACCURACY_THRESHOLD:          # the gate after tuning
            result = {"run_id": run_id, "status": "failed_gate", "metrics": metrics, "tuned": tuned}
            print(json.dumps(result, indent=2))
            return result

    registered = ray.get(register_model.remote(run_id))

    if not ray.get(check_human_approval.remote(metrics, force=approve)):
        result = {"run_id": run_id, "status": "pending_approval", "metrics": metrics, "tuned": tuned,
                  "register": registered}
        print(json.dumps(result, indent=2))
        return result

    deploy_status = ray.get(deploy_model.remote(run_id))
    result = {"run_id": run_id, "status": "completed", "metrics": metrics, "tuned": tuned,
              "register": registered, "deploy": deploy_status}
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-id", default="local-demo")
    parser.add_argument("--approve", action="store_true",
                        help="Simulate human approval (or create approvals/production.flag)")
    args = parser.parse_args()
    run_pipeline(args.run_id, approve=args.approve)


if __name__ == "__main__":
    main()
