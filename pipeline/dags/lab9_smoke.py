"""lab9_smoke - the first DAG of the week-9 lab: proves the three connections before the real pipeline.

  hello_pod  -> a pod from the lab image runs in the cluster and returns a value through XCom
  ray_ping   -> a pod submits a tiny job to the Ray cluster and waits for it
  approve    -> a human approves in the UI (Required Actions); who and when is recorded
  done       -> an ordinary Python task reads the XCom value
"""
from datetime import timedelta

from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.standard.operators.hitl import ApprovalOperator
from airflow.sdk import dag, task

IMAGE = "fraud-train:lab9"
MLFLOW = {"MLFLOW_TRACKING_URI": "http://mlflow.mlops.svc:5000"}


@dag(schedule=None, catchup=False, tags=["lab9"])
def lab9_smoke():
    hello = KubernetesPodOperator(
        task_id="hello_pod", name="hello-pod", namespace="airflow",
        image=IMAGE, image_pull_policy="IfNotPresent", in_cluster=True,
        deferrable=True, logging_interval=20,
        cmds=["sh", "-c"],
        arguments=["python -c \"import ray, mlflow, sklearn, json; "
                   "print('hello from a pod'); "
                   "json.dump({'ray': ray.__version__, 'mlflow': mlflow.__version__, 'sklearn': sklearn.__version__}, "
                   "open('/airflow/xcom/return.json', 'w'))\""],
        env_vars=MLFLOW, do_xcom_push=True,
        retries=1, retry_delay=timedelta(seconds=15),
    )
    ray_ping = KubernetesPodOperator(
        task_id="ray_ping", name="ray-ping", namespace="airflow",
        image=IMAGE, image_pull_policy="IfNotPresent", in_cluster=True,
        deferrable=True, logging_interval=20,
        cmds=["sh", "-c"],
        arguments=["python pipeline/ray_jobs/submit_job.py --follow --entrypoint "
                   "\"python -c 'import ray; ray.init(); print(\\\"ray cluster:\\\", ray.cluster_resources())'\""],
        env_vars=MLFLOW,
        retries=1, retry_delay=timedelta(seconds=15),
    )
    approve = ApprovalOperator(task_id="approve", subject="lab9_smoke: everything worked - continue?")

    @task
    def done(versions):
        print("the pod reported:", versions)

    [hello, ray_ping] >> approve >> done(hello.output)


lab9_smoke()
