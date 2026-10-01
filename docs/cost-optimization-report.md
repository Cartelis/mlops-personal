# Cost Optimization Report — Week 12

## Baseline (on-demand, 5 replicas)

| Item | Value |
|------|-------|
| Replicas | 5 |
| vCPU per replica | 0.25 |
| Pricing model | on-demand |
| Monthly compute (est.) | Run `python scripts/tco_calculator.py --baseline` |

## Optimized (spot + rightsizing + autoscaling)

| Item | Value |
|------|-------|
| Peak replicas (load test) | 32 |
| Spot / preemptible | yes |
| Rightsizing | yes (requests match actual usage) |
| Monthly compute (est.) | Run `python scripts/tco_calculator.py --replicas 32 --spot --rightsizing` |

## Savings summary

| Metric | Baseline | Optimized | Change |
|--------|----------|-----------|--------|
| Monthly compute USD | _fill_ | _fill_ | _fill_% |
| Cost per request | _fill_ | _fill_ | _fill_% |
| Meets 60% target | — | — | yes/no |

## Uptime during scaling

| Event | Replicas | p95 latency | Errors | Notes |
|-------|----------|-------------|--------|-------|
| Load test ramp 1→50 users | _fill_ | _fill_ | _fill_ | Locust report |
| Scale down after test | _fill_ | _fill_ | _fill_ | HPA cooldown |

## Decisions

_(Team rationale: why spot is acceptable for fraud API, PDB settings, min replicas in production.)_