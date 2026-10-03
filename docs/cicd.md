# CI/CD Pipeline - Week 6

## Pipeline stages

```
lint -> test -> model-gate -> build-push -> ArgoCD sync
```

| Job | Trigger | Purpose |
|-----|---------|---------|
| lint | PR + main | `ruff check` |
| test | PR + main | `pytest tests/` |
| model-gate | PR + main | accuracy >= 0.95 |
| build-push | main only | Docker push + manifest bump |

## GitHub Actions

Workflow: `.github/workflows/ml-pipeline.yml`

```bash
# Local checks before push
pip install -r requirements.txt -r requirements-dev.txt
python scripts/bootstrap.py && python src/evaluate.py
pytest tests/ -v
python scripts/check_model_gate.py --threshold 0.95
```

## ArgoCD (GitOps)

```bash
kubectl apply -f deploy/argocd/application.yaml
argocd app sync mlops-fraud-api
argocd app get mlops-fraud-api
```

## Rollback

### Option A: Git revert (preferred)

```bash
git revert <commit-that-bumped-image>
git push origin main
# ArgoCD auto-syncs previous image
```

### Option B: ArgoCD history

```bash
argocd app history mlops-fraud-api
argocd app rollback mlops-fraud-api <revision>
```

### Option C: Manual image pin

Edit `k8s/deployment-cpu.yaml` to pin a known good tag, commit and push.

## Canary (simplified)

- Staging overlay: `deploy/overlays/staging` (1 replica)
- Production overlay: `deploy/overlays/production` (3 replicas)
- Full traffic split: KServe / Argo Rollouts (weeks 7-8)