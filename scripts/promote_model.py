"""Register and promote the fraud model with MLflow aliases - the pipeline's two registry steps.

  register  create a model version from a training run and give it the alias `candidate`.
            Idempotent: a run that was already registered (found by its tag) gets no second version.
  promote   move an alias (default `champion`) to the `candidate` version - the deployment step
            under a service that loads models:/fraud-detector@champion.

  python scripts/promote_model.py register --run-id-file models/run_id.txt --tag airflow_run_id=manual__2026-10-28
  python scripts/promote_model.py promote --to champion

Week 7's scripts/register_model.py uses registry *stages*; this script uses *aliases* (the current
MLflow API, also used by week 2 and assignment U2) and never re-logs the model, so the version keeps
its link to the training run (lineage, NFR-09).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import mlflow
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException

MODEL_NAME = "fraud-detector"
ROOT = Path(__file__).resolve().parents[1]


def _require_tracking_uri() -> None:
    if not os.environ.get("MLFLOW_TRACKING_URI"):
        sys.exit("MLFLOW_TRACKING_URI is not set - refusing to register into a local ./mlruns by accident")


def _find_version_by_tag(client: MlflowClient, key: str, value: str):
    """Model versions carrying tag key=value (the pipeline's idempotency key)."""
    try:
        versions = client.search_model_versions(f"name = '{MODEL_NAME}' and tag.{key} = '{value}'")
    except MlflowException:
        versions = []
    return sorted(versions, key=lambda v: int(v.version))


def register(args: argparse.Namespace) -> None:
    run_id = args.run_id or Path(args.run_id_file).read_text().strip()
    tags = dict(kv.split("=", 1) for kv in args.tag)
    client = MlflowClient()

    if tags:
        key, value = next(iter(tags.items()))
        existing = _find_version_by_tag(client, key, value)
        if existing:
            v = existing[-1]
            print(f"already registered: {MODEL_NAME} version {v.version} carries {key}={value} - skipping")
            _write_result(args, v.version, run_id, created=False)
            return

    mv = mlflow.register_model(f"runs:/{run_id}/model", MODEL_NAME)
    for key, value in tags.items():
        client.set_model_version_tag(MODEL_NAME, mv.version, key, value)
        client.set_tag(run_id, key, value)                      # the run knows which pipeline run produced it
    client.set_model_version_tag(MODEL_NAME, mv.version, "source_run_id", run_id)
    if args.alias:
        client.set_registered_model_alias(MODEL_NAME, args.alias, mv.version)
    print(f"registered {MODEL_NAME} version {mv.version} from run {run_id}; alias @{args.alias}")
    _write_result(args, mv.version, run_id, created=True)


def promote(args: argparse.Namespace) -> None:
    client = MlflowClient()
    try:
        src = client.get_model_version_by_alias(MODEL_NAME, args.from_alias)
    except MlflowException as exc:
        sys.exit(f"no version carries alias @{args.from_alias}: {exc}")
    client.set_registered_model_alias(MODEL_NAME, args.to, src.version)
    for kv in args.tag:
        key, value = kv.split("=", 1)
        client.set_model_version_tag(MODEL_NAME, src.version, key, value)
    print(f"promoted {MODEL_NAME} version {src.version}: @{args.from_alias} -> @{args.to}")
    _write_result(args, src.version, src.run_id, created=False)


def _write_result(args: argparse.Namespace, version: str, run_id: str, created: bool) -> None:
    """Small JSON for the orchestrator (Airflow reads /airflow/xcom/return.json from the pod)."""
    if args.result:
        Path(args.result).parent.mkdir(parents=True, exist_ok=True)
        Path(args.result).write_text(json.dumps({"model": MODEL_NAME, "version": int(version),
                                                 "run_id": run_id, "created": created}) + "\n")


def main() -> None:
    _require_tracking_uri()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("register", help="create a version from a run (idempotent by --tag)")
    p.add_argument("--run-id", help="training run id (default: read --run-id-file)")
    p.add_argument("--run-id-file", default=str(ROOT / "models/run_id.txt"))
    p.add_argument("--alias", default="candidate")
    p.add_argument("--tag", action="append", default=[], metavar="KEY=VALUE",
                   help="tag on the version and the run; the first one is the idempotency key")
    p.add_argument("--result", help="write a JSON summary here (XCom)")
    p.set_defaults(func=register)

    p = sub.add_parser("promote", help="move an alias to the candidate version")
    p.add_argument("--from-alias", default="candidate")
    p.add_argument("--to", default="champion")
    p.add_argument("--tag", action="append", default=[], metavar="KEY=VALUE", help="e.g. approved_by=...")
    p.add_argument("--result", help="write a JSON summary here (XCom)")
    p.set_defaults(func=promote)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
