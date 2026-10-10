# ML Pipeline DAG - Week 9

## Ray pipeline flow

```mermaid
flowchart TD
    A[ingest_data] --> B[preprocess]
    B --> C[train_model]
    C --> D[evaluate_model]
    D -->|accuracy < 0.95| E[tune_hyperparams]
    E --> C
    D -->|accuracy >= 0.95| F[register_model]
    E --> F
    F --> G{human_approval}
    G -->|approved| H[deploy_model]
    G -->|pending| I[stop pending_approval]
```

## Stages

| Stage | Ray task | Script |
|-------|----------|--------|
| Ingest | `ingest_data` | `scripts/bootstrap.py` |
| Preprocess | `preprocess` | `src/prepare_data.py` |
| Train | `train_model` | `src/train.py` |
| Evaluate | `evaluate_model` | `src/evaluate.py` |
| Tune (conditional) | `tune_hyperparams` | params override |
| Register | `register_model` | `scripts/register_model.py` |
| Approve (HITL) | `check_human_approval` | `approvals/production.flag` |
| Deploy | `deploy_model` | GitOps hook (week 6) |

## Run

```bash
ray start --head
python pipeline/ray_pipeline.py --run-id exp-001
touch approvals/production.flag
python pipeline/ray_pipeline.py --run-id exp-001 --approve
```