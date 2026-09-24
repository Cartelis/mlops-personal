# Cost Analysis - Week 4

## Assumptions

- Region: europe-west1
- Requests: 1000/day, avg 80ms, 512Mi RAM
- Storage: 5 GB GCS, 2 GB Artifact Registry

## Monthly estimate

| Service | Estimate USD/month |
|---------|-------------------|
| Cloud Run | 15-40 |
| GCS | 0.10-1 |
| Artifact Registry | 0.20-2 |
| **Total** | **~20-45** |

## Managed vs self-managed

| Option | Setup | Ops/month | TCO (est.) |
|--------|-------|-----------|------------|
| Cloud Run | 2h | Low | $20-45 |
| Vertex Endpoint | 4h | Low | $80-200 |
| GKE (2 nodes) | 2d | High | $150-350 |

## Decision

We chose Cloud Run because: _(team rationale)_