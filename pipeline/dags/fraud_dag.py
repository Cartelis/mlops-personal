"""fraud_pipeline - the retraining night of the fraud model as an Airflow 3 DAG (week 9).

    ingest -> prepare -> train -> evaluate -> gate -+-> register -> approve -> promote -> deploy -> smoke_test
                                                    +-> tune (Ray) -^
Every step that touches data or a model is a pod started from the lab image (KubernetesPodOperator);
`tune` submits a Ray Tune job to the KubeRay cluster; `gate` and `deploy` are Airflow's own tasks;
`approve` waits for a person. MLflow is the shared memory between the steps.

Parameters ("Trigger DAG w/ config"):
    threshold   accuracy the model must reach (0.95)
    max_depth   tree depth for the first training (5; try 1 to force the tune branch)
    n_estimators trees for the first training (100)
"""
from datetime import timedelta

from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.standard.operators.hitl import ApprovalOperator
from airflow.sdk import Param, dag, task
from kubernetes.client import models as k8s

IMAGE = "fraud-train:lab9"
NAMESPACE = "airflow"
MLFLOW = {
    "MLFLOW_TRACKING_URI": "http://mlflow.mlops.svc:5000",
    "MLFLOW_EXPERIMENT_NAME": "fraud-detection",
    # Fail fast inside the step (the MLflow client would otherwise retry for minutes on its own);
    # retrying with back-off is the orchestrator's job, where every attempt is visible.
    "MLFLOW_HTTP_REQUEST_MAX_RETRIES": "2",
    "MLFLOW_HTTP_REQUEST_TIMEOUT": "10",
}
# The shared working volume: data/ and models/ of every pod (and of the Ray cluster) are the same files.
WORK = k8s.V1Volume(name="work", persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name="fraud-work"))
MOUNTS = [
    k8s.V1VolumeMount(name="work", mount_path="/work/data", sub_path="data"),
    k8s.V1VolumeMount(name="work", mount_path="/work/models", sub_path="models"),
]
RESOURCES = k8s.V1ResourceRequirements(requests={"cpu": "250m", "memory": "256Mi"}, limits={"memory": "1Gi"})


def fraud_pod(task_id: str, command: str, **kw) -> KubernetesPodOperator:
    """One helper, identical plumbing for every step: image, volume, MLflow address, retries."""
    kw = {"retries": 2, "retry_delay": timedelta(seconds=20), "retry_exponential_backoff": True,
          "execution_timeout": timedelta(minutes=15),   # no step may hang forever (observability principle)
          "deferrable": True, "logging_interval": 20,   # wait in the triggerer, fetch the pod log every 20 s:
                                                        # no long-lived log stream to hang, no worker slot held
          "in_cluster": True,                   # the trigger needs this to use the triggerer's service account
          "on_finish_action": "keep_pod",       # finished pods stay visible in `kubectl get pods`
          **kw}                                 # a step may override any of these (e.g. retries=0)
    return KubernetesPodOperator(
        task_id=task_id, name=task_id.replace("_", "-"), namespace=NAMESPACE,
        image=IMAGE, image_pull_policy="IfNotPresent",
        cmds=["sh", "-c"], arguments=[command],
        env_vars=MLFLOW, volumes=[WORK], volume_mounts=MOUNTS, container_resources=RESOURCES,
        **kw,
    )


@dag(
    schedule=None,                              # started by hand in the lab; "0 2 * * *" in production
    catchup=False,
    max_active_runs=1,                          # two nights must not write the same volume at once
    tags=["lab9"],
    doc_md=__doc__,
    params={
        "threshold": Param(0.95, type="number", description="accuracy the model must reach"),
        "max_depth": Param(5, type="integer", description="tree depth of the first training"),
        "n_estimators": Param(100, type="integer", description="trees of the first training"),
    },
)
def fraud_pipeline():
    ingest = fraud_pod("ingest", "python src/ingest.py")
    prepare = fraud_pod("prepare", "python src/prepare_data.py")
    train = fraud_pod(
        "train",
        "python src/train.py --max_depth {{ params.max_depth }} --n_estimators {{ params.n_estimators }}",
    )
    evaluate = fraud_pod(
        "evaluate",
        "python src/evaluate.py && cp metrics.json /airflow/xcom/return.json",   # a few bytes back to Airflow
        do_xcom_push=True,
    )

    @task.branch
    def gate(metrics: dict, **context) -> str:
        """Branch on a value measured during the run, not on a guess made when the DAG was written."""
        threshold = float(context["params"]["threshold"])
        accuracy = float(metrics["accuracy"])
        print(f"accuracy={accuracy:.4f} threshold={threshold} -> {'register' if accuracy >= threshold else 'tune'}")
        return "register" if accuracy >= threshold else "tune"

    tune = fraud_pod(
        "tune",
        # Ray Tune on the KubeRay cluster, then the usual evaluation and the week-6 quality gate.
        "python pipeline/ray_jobs/submit_job.py --follow --entrypoint "
        "\"python /work/pipeline/ray_jobs/tune_fraud.py --tag airflow_run_id={{ run_id }}\" && "
        "python src/evaluate.py && "
        "python scripts/check_model_gate.py --threshold {{ params.threshold }}",
        retries=0,                              # a model below the threshold is not a transient failure
    )
    register = fraud_pod(
        "register",
        "python scripts/promote_model.py register --alias candidate "
        "--tag airflow_run_id={{ run_id }} --result /airflow/xcom/return.json",
        do_xcom_push=True,
        trigger_rule="none_failed_min_one_success",   # the two paths rejoin here
    )
    approve = ApprovalOperator(
        task_id="approve",
        subject="Promote fraud-detector to @champion?",
        body="Pipeline run {{ run_id }}. Check the candidate version in MLflow before deciding.",
    )
    promote = fraud_pod(
        "promote",
        "python scripts/promote_model.py promote --to champion --tag approved_in_run={{ run_id }}",
    )

    @task
    def deploy() -> dict:
        """Restart the model service so it loads models:/fraud-detector@champion, and wait for the rollout."""
        import time
        from datetime import datetime, timezone

        from kubernetes import client, config

        try:
            config.load_incluster_config()      # Airflow runs inside the cluster (Helm chart)
        except config.ConfigException:
            config.load_kube_config()           # or on a laptop (airflow standalone)
        apps = client.AppsV1Api()
        name, namespace = "fraud-api", "mlops"
        stamp = datetime.now(timezone.utc).isoformat()
        apps.patch_namespaced_deployment(name, namespace, {
            "spec": {"template": {"metadata": {"annotations": {"kubectl.kubernetes.io/restartedAt": stamp}}}}
        })
        print(f"rollout restart of {namespace}/{name} at {stamp}")
        for _ in range(60):
            d = apps.read_namespaced_deployment(name, namespace)
            s, want = d.status, d.spec.replicas
            if (s.observed_generation or 0) >= d.metadata.generation and (s.updated_replicas or 0) == want \
                    and (s.ready_replicas or 0) == want and (s.replicas or 0) == want:
                print("rollout complete: the service now answers with the champion model")
                return {"deployment": f"{namespace}/{name}", "restarted_at": stamp}
            time.sleep(5)
        raise RuntimeError("rollout did not complete within 5 minutes - kubectl -n mlops describe deploy fraud-api")

    smoke_test = fraud_pod(
        "smoke_test",
        "python scripts/smoke_test_api.py --url http://fraud-api.mlops.svc/predict --result /airflow/xcom/return.json",
        do_xcom_push=True,
    )

    decision = gate(evaluate.output)
    ingest >> prepare >> train >> evaluate >> decision
    decision >> [register, tune]
    tune >> register >> approve >> promote >> deploy() >> smoke_test


fraud_pipeline()
