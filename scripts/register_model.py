"""Register fraud model in MLflow Model Registry and promote to Production."""
import argparse
import os

import joblib
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient

MODEL_NAME = "fraud-detector"


def register_from_run(run_id: str) -> int:
    result = mlflow.register_model(f"runs:/{run_id}/model", MODEL_NAME)
    return int(result.version)


def register_from_local(model_path: str = "models/model.pkl") -> int:
    """Log local model and register when no MLflow run exists."""
    mlflow.set_experiment("mlops-semester-project")
    with mlflow.start_run(run_name="registry-bootstrap") as run:
        model = joblib.load(model_path)
        mlflow.sklearn.log_model(model, "model")
        mlflow.log_param("source", "local_register_script")
        run_id = run.info.run_id
    result = mlflow.register_model(f"runs:/{run_id}/model", MODEL_NAME)
    return int(result.version)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=os.environ.get("MLFLOW_RUN_ID"))
    parser.add_argument("--model-path", default="models/model.pkl")
    parser.add_argument("--skip-promote", action="store_true")
    args = parser.parse_args()

    uri = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    mlflow.set_tracking_uri(uri)

    if args.run_id:
        version = register_from_run(args.run_id)
    else:
        version = register_from_local(args.model_path)

    print(f"Registered {MODEL_NAME} version {version}")

    if args.skip_promote:
        return

    client = MlflowClient()
    client.transition_model_version_stage(MODEL_NAME, version, "Staging")
    print(f"Promoted v{version} to Staging")
    client.transition_model_version_stage(MODEL_NAME, version, "Production")
    print(f"Promoted v{version} to Production")


if __name__ == "__main__":
    main()