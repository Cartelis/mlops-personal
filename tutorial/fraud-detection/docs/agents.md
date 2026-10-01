# MLOps Self-Healing Agent - Week 10

## Architecture

LangGraph state machine with tools:

- `check_drift` — PSI on feature `f0`
- `run_retrain` — Ray pipeline (week 9)
- `model_gate` — accuracy >= 0.95
- `deploy` — GitOps hook
- `notify_slack` — webhook or `docs/slack-mock.txt`

## Flow

```
monitor -> (drift?) -> retrain -> model_gate -> approval -> deploy -> notify
```

## Run demo

```bash
pip install -r requirements-agents.txt -r requirements-orchestration.txt
export MLFLOW_TRACKING_URI=sqlite:///mlflow.db

python scripts/bootstrap.py
python scripts/simulate_drift.py
python -m agents.mlops_agent --incident-id DR-2026-001

touch approvals/production.flag
python -m agents.mlops_agent --incident-id DR-2026-001 --approve

cat docs/agent-audit.log
cat docs/slack-mock.txt
```

## Guardrails

| Guardrail | Implementation |
|-----------|----------------|
| HITL before deploy | `approvals/production.flag` |
| Model gate | accuracy >= 0.95 |
| Retrain limit | <= 3 per day (`docs/agent-retrain-count.json`) |
| Audit | `docs/agent-audit.log` (JSON lines) |

## Optional: Slack

```bash
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```