"""Production-style Ray ML pipeline for week 9 orchestration lab."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import ray

ACCURACY_THRESHOLD = 0.95
APPROVAL_FILE = Path("approvals/production.flag")
ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


@ray.remote(num_cpus=1, max_retries=2, retry_exceptions=True)
def ingest_data(raw_path: str = "data/raw/dataset.csv") -> str:
    path = ROOT / raw_path
    if not path.exists():
        _run([sys.executable, "scripts/bootstrap.py"])
    return raw_path


@ray.remote(num_cpus=1, max_retries=2, retry_exceptions=True)
def preprocess(_raw_path: str) -> dict[str, str]:
    _run([sys.executable, "src/prepare_data.py"])
    return {
        "train": "data/processed/train.csv",
        "test": "data/processed/test.csv",
    }


@ray.remote(num_cpus=1, max_retries=2, retry_exceptions=True)
def train_model(params: dict | None = None) -> str:
    cmd = [sys.executable, "src/train.py"]
    if params and "n_estimators" in params:
        cmd += ["--n_estimators", str(params["n_estimators"])]
    _run(cmd)
    return "models/model.pkl"


@ray.remote(num_cpus=1)
def evaluate_model(_model_path: str) -> dict:
    _run([sys.executable, "src/evaluate.py"])
    with open(ROOT / "metrics.json") as f:
        return json.load(f)


@ray.remote(num_cpus=1)
def tune_hyperparams() -> dict:
    return {"n_estimators": 300, "reason": "accuracy below threshold"}


@ray.remote(num_cpus=1)
def register_model(skip_promote: bool = True) -> str:
    cmd = [sys.executable, "scripts/register_model.py"]
    if skip_promote:
        cmd.append("--skip-promote")
    _run(cmd)
    return "registered"


@ray.remote(num_cpus=0)
def check_human_approval(metrics: dict, force: bool = False) -> bool:
    if force or APPROVAL_FILE.exists():
        return True
    print(
        f"PENDING HUMAN APPROVAL: accuracy={metrics.get('accuracy', 0):.4f}\n"
        f"Create {APPROVAL_FILE} or re-run with --approve"
    )
    return False


@ray.remote(num_cpus=0)
def deploy_model() -> str:
    # Hook for week 6 CI/CD: e.g. trigger manifest bump or ArgoCD sync
    return "deploy-triggered-via-gitops"


def run_pipeline(run_id: str, approve: bool = False) -> dict:
    ray.init(ignore_reinit_error=True)
    print(f"Starting Ray pipeline run_id={run_id}")

    raw = ray.get(ingest_data.remote())
    _paths = ray.get(preprocess.remote(raw))
    model_path = ray.get(train_model.remote())
    metrics = ray.get(evaluate_model.remote(model_path))
    tuned = False

    if metrics.get("accuracy", 0) < ACCURACY_THRESHOLD:
        print(f"Accuracy {metrics['accuracy']:.4f} < {ACCURACY_THRESHOLD}, tuning...")
        tune_params = ray.get(tune_hyperparams.remote())
        model_path = ray.get(train_model.remote(tune_params))
        metrics = ray.get(evaluate_model.remote(model_path))
        tuned = True

    register_status = ray.get(register_model.remote())

    if not ray.get(check_human_approval.remote(metrics, force=approve)):
        result = {
            "run_id": run_id,
            "status": "pending_approval",
            "metrics": metrics,
            "tuned": tuned,
            "register": register_status,
        }
        print(json.dumps(result, indent=2))
        return result

    deploy_status = ray.get(deploy_model.remote())
    result = {
        "run_id": run_id,
        "status": "completed",
        "metrics": metrics,
        "tuned": tuned,
        "register": register_status,
        "deploy": deploy_status,
    }
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default="local-demo")
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Simulate human approval (or use approvals/production.flag)",
    )
    args = parser.parse_args()
    run_pipeline(args.run_id, approve=args.approve)


if __name__ == "__main__":
    main()