# Orchestration - Week 9

## Tool choice

The retraining pipeline is an **Apache Airflow 3** DAG (`pipeline/dags/fraud_dag.py`) whose steps run as
pods in the Kubernetes cluster; the hyperparameter search inside the `tune` step runs on a small **Ray**
cluster (KubeRay). The division of labour: Airflow holds the night (schedule, state, retries, branch,
human approval, one place to look); Ray is the compute engine inside the step that needs parallelism.

| Layer | Tool | Why here |
|-------|------|----------|
| Control plane (DAG scheduler) | Airflow 3.2.2, Helm chart 1.22.0, LocalExecutor | the tool most teams already run; HITL operator since 3.1; tasks isolated from the scheduler (Task SDK); governed by the Apache Software Foundation |
| Data plane | pods from one image `fraud-train:lab9` (`docker/Dockerfile.train`) | "Airflow decides, containers compute" - the scheduler never imports scikit-learn |
| Compute engine (one step) | Ray 2.59 via KubeRay 1.7.1, `RayCluster fraud-ray` | Ray Tune grid search over `n_estimators x max_depth`; the same job scales to a real cluster unchanged |
| Shared memory between steps | MLflow 3.15.2 in the cluster (`http://mlflow.mlops.svc:5000`) | runs, metrics, model versions, aliases `@candidate` -> `@champion` |
| Serving | `fraud-api` (week-3 FastAPI app) loading `models:/fraud-detector@champion` | moving the alias *is* the deployment; the `deploy` task restarts the service |

## Comparison

| Tool | Strength | Why not primary here |
|------|----------|----------------------|
| **DVC** (week 2) | data/model versioning, local DAG | no schedule, no retries, no human wait, one machine |
| **GitHub Actions** (week 6) | release path with a quality gate | triggered by a push, no branch on a run-time metric, no 8-hour wait |
| **Kubernetes Job** (week 5) | one container, once | no ordering, no conditions, no history |
| **Ray alone** (`pipeline/ray_pipeline.py`) | fine-grained parallel tasks, Ray Train/Tune | a DAG without a control plane: no schedule, state, retry history or audit - "an engine without a gearbox" |
| **Dagster** | asset-centric lineage, light locally | the organisation question: most teams inherit Airflow |
| **Kubeflow Pipelines** | typed, cached, Kubernetes-native platform | a platform to operate (~3.5 GB for pipelines alone) |

## Human in the loop

`approve` is an `ApprovalOperator` (Airflow >= 3.1): the run pauses under *Required Actions*; whoever
clicks Approve/Reject is stored with the task instance together with the time (`responded_by`,
`responded_at`) - the audit trail. A rejection fails the task, nothing downstream runs, and the model
version keeps its `candidate` alias. The Ray-only script keeps the older file-flag mechanism
(`approvals/production.flag` or `--approve`) because week 10's agent calls it; its approvals are appended
to `approvals/log.md`.

## Running it

```bash
scripts/lab9/00_preflight.sh      # tools + images (at home)
scripts/lab9/01_build_image.sh    # fraud-train:lab9
scripts/lab9/02_cluster_up.sh     # kind cluster lab9 with pipeline/dags mounted
scripts/lab9/03_mlflow.sh  scripts/lab9/04_airflow.sh  scripts/lab9/05_ray.sh  scripts/lab9/06_fraud_api.sh
scripts/lab9/07_portforward.sh    # MLflow :5001, Airflow :8082, Ray :8265, fraud-api :8088
scripts/lab9/08_trigger_run.sh A  # then: watch | approve | B | C | status | logs
scripts/lab9/09_inference_test.sh
scripts/lab9/99_down.sh
```

Without a cluster: `pip install -r requirements-orchestration.txt`, `export MLFLOW_TRACKING_URI=...`,
`python pipeline/ray_pipeline.py --run-id <id> [--approve]`.

## NFR mapping (requirements.md v1.8)

- NFR-34: pipeline end to end <= 10 min on the lab cluster (measured: run A 1.5 min, run B with Ray Tune see `docs/pipeline-dag.md`)
- NFR-35: the tune branch runs if and only if accuracy < `params.threshold` (run B vs run A)
- NFR-36: 100 % of promotions pass `ApprovalOperator`; user + timestamp recorded
- NFR-37: re-running `register` creates no duplicate version (tag `airflow_run_id` is the idempotency key)
