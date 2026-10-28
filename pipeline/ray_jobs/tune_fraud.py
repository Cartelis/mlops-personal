"""Hyperparameter search for the fraud model with Ray Tune - the pipeline's `tune` step as a Ray job.

Submitted by the tune pod of the Airflow DAG (pipeline/ray_jobs/submit_job.py); runs on the KubeRay
cluster, whose pods mount the pipeline's shared volume at /work/data and /work/models.

  1. Trials: every (n_estimators, max_depth) pair of the grid trains a RandomForest on the prepared
     train split and reports its accuracy on the test split; trials run in parallel, one CPU each,
     and each logs a small MLflow run (tagged ray_trial_id) in the same experiment as the pipeline.
  2. The best pair is trained once more with the week-2 script src/train.py, so the model, its
     MLflow run (lineage tags, logged model) and models/run_id.txt are exactly what the following
     evaluate -> register steps expect. Nothing downstream knows that Ray was involved.

  python pipeline/ray_jobs/tune_fraud.py --tag airflow_run_id=manual__2026-10-28T10:00:00
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import mlflow
import pandas as pd
import ray
from ray import tune
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

ROOT = Path(__file__).resolve().parents[2]          # /work inside the lab image
DATA = ROOT / "data/processed"


def trial(config: dict) -> None:
    """One Ray Tune trial: train, score, report. Runs on any node of the Ray cluster."""
    train = pd.read_csv(DATA / "train.csv")
    test = pd.read_csv(DATA / "test.csv")
    model = RandomForestClassifier(
        n_estimators=config["n_estimators"], max_depth=config["max_depth"], random_state=config["seed"]
    )
    model.fit(train.drop("target", axis=1), train["target"])
    acc = accuracy_score(test["target"], model.predict(test.drop("target", axis=1)))

    if os.environ.get("MLFLOW_TRACKING_URI"):      # every trial is an experiment run too
        mlflow.set_experiment(config["experiment"])
        with mlflow.start_run(run_name=f"tune-n{config['n_estimators']}-d{config['max_depth']}"):
            mlflow.log_params({k: config[k] for k in ("n_estimators", "max_depth", "seed")})
            mlflow.log_metric("accuracy", acc)
            mlflow.set_tags({"stage": "tune", "ray_trial_id": tune.get_context().get_trial_id(), **config["tags"]})
    tune.report({"accuracy": acc})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-estimators", default="50,100,200,300")
    parser.add_argument("--max-depth", default="3,6,12")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--cpus-per-trial", type=float, default=1)
    parser.add_argument("--experiment", default=os.environ.get("MLFLOW_EXPERIMENT_NAME", "fraud-detection"))
    parser.add_argument("--tag", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()
    tags = dict(kv.split("=", 1) for kv in args.tag)

    ray.init(address="auto")
    print("Ray cluster resources:", ray.cluster_resources(), flush=True)

    space = {
        "n_estimators": tune.grid_search([int(v) for v in args.n_estimators.split(",")]),
        "max_depth": tune.grid_search([int(v) for v in args.max_depth.split(",")]),
        "seed": args.seed,
        "experiment": args.experiment,
        "tags": tags,
    }
    tuner = tune.Tuner(
        tune.with_resources(trial, {"cpu": args.cpus_per_trial}),
        param_space=space,
        tune_config=tune.TuneConfig(metric="accuracy", mode="max"),
        run_config=tune.RunConfig(name="fraud-tune", storage_path="/tmp/ray_results", verbose=1),
    )
    results = tuner.fit()
    best = results.get_best_result()
    print(f"\n{len(results)} trials; best accuracy={best.metrics['accuracy']:.4f} "
          f"with n_estimators={best.config['n_estimators']} max_depth={best.config['max_depth']}", flush=True)

    # The winner, trained once more by the week-2 script so the rest of the pipeline is unchanged.
    cmd = [sys.executable, "src/train.py",
           "--n_estimators", str(best.config["n_estimators"]), "--max_depth", str(best.config["max_depth"])]
    print("retraining the best configuration:", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)
    run_id = (ROOT / "models/run_id.txt").read_text().strip()
    if tags and os.environ.get("MLFLOW_TRACKING_URI"):
        mlflow.MlflowClient().set_tag(run_id, "stage", "tune-best")
        for key, value in tags.items():
            mlflow.MlflowClient().set_tag(run_id, key, value)
    summary = {"trials": len(results), "best_accuracy": best.metrics["accuracy"], "best_config":
               {"n_estimators": best.config["n_estimators"], "max_depth": best.config["max_depth"]}, "run_id": run_id}
    (ROOT / "models/tune_result.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("TUNE_RESULT", json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
