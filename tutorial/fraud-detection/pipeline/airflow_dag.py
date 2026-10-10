"""Reference Airflow DAG for comparison with Ray (week 9).

Requires Apache Airflow installed. Not the primary lab deliverable.
"""
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="fraud_ml_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["mlops", "fraud"],
) as dag:
    prepare = BashOperator(
        task_id="prepare",
        bash_command="python src/prepare_data.py",
    )
    train = BashOperator(
        task_id="train",
        bash_command="python src/train.py",
    )
    evaluate = BashOperator(
        task_id="evaluate",
        bash_command="python src/evaluate.py",
    )
    register = BashOperator(
        task_id="register",
        bash_command="python scripts/register_model.py --skip-promote",
    )

    prepare >> train >> evaluate >> register