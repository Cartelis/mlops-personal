# Orchestration - Week 9

## Tool choice

We use **Ray** as the primary orchestrator because:

- Python-native `@ray.remote` tasks map cleanly to ML steps
- Same runtime locally and on HPC Ray cluster
- Easy conditional branching and retries
- Integrates with existing `src/` scripts and MLflow

## Comparison

| Tool | Strength | Limitation for our project |
|------|----------|----------------------------|
| **DVC** (week 2) | Data/model versioning | No scheduling, no HITL |
| **GitHub Actions** (week 6) | CI/CD gates | Not full ML DAG orchestration |
| **Airflow** | Cron, enterprise ops | Heavier ML metadata integration |
| **Prefect** | Modern Python flows | Less distributed compute focus |
| **Dagster** | Asset lineage | Steeper platform setup |
| **Ray** | Distributed ML tasks | Chosen for lab deliverable |

## Human-in-the-loop

Production deploy requires `approvals/production.flag` or `--approve` flag (demo only).

Audit: commit approval decision to Git or log approver in MLflow tags (governance week 16).

## NFR mapping

- NFR-34: Pipeline runtime <= 30 min
- NFR-35: Tune branch if accuracy < 0.95
- NFR-36: 100% prod deploys approved
- NFR-37: Idempotent re-runs