# Federated Learning Report — Week 14

## Setup

| Parameter | Value |
|-----------|-------|
| Framework | Flower (FedAvg algorithm) |
| Clients | 3 |
| Rounds | 5 |
| Model | LogisticRegression (federated weights) |
| Data | `data/federated/client_*` partitions |

## Results

Run:

```bash
python -m federated.partition_data --clients 3
python -m federated.fl_simulation --rounds 5 --clients 3
```

Fill from `docs/fl-results.json`:

| Metric | Value |
|--------|-------|
| Centralized accuracy | _ |
| Federated test accuracy | _ |
| Gap (pp) | _ |
| Meets <= 2 pp target | yes/no |

## Privacy rationale

- Raw transaction rows stay on client partitions; only model weights aggregated.
- Suitable when GDPR/regulator restricts cross-border raw data pooling.

## Communication cost (estimate)

| Item | Estimate |
|------|----------|
| Params per round | ~80 floats (coef + intercept) |
| Rounds | 5 |
| Total upload/client | _ KB |

## Optional Flower Ray engine

```bash
python -m federated.fl_simulation --engine flower --rounds 3 --clients 3
```

Uses `fl.simulation.start_simulation` with Ray (slower; closer to production Flower).