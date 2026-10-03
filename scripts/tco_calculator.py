"""TCO calculator for fraud API: on-demand vs spot vs rightsizing (week 12)."""
from __future__ import annotations

import argparse
import json

# Lab defaults (USD/month per vCPU for illustration)
ON_DEMAND_VCPU_MONTH = 30.0
SPOT_DISCOUNT = 0.65
RIGHTSIZING_SAVINGS = 0.20
BASELINE_REPLICAS = 5
PEAK_REPLICAS = 32
AVG_REPLICAS_OPTIMIZED = 8
REQUESTS_PER_MONTH = 1_000_000
VCPU_PER_REPLICA = 0.25
MONTH_HOURS = 730


def monthly_compute_cost(
    replicas: int,
    spot: bool = False,
    rightsizing: bool = False,
) -> dict:
    vcpu_hours = replicas * VCPU_PER_REPLICA * MONTH_HOURS
    rate = ON_DEMAND_VCPU_MONTH / MONTH_HOURS
    cost = vcpu_hours * rate
    if spot:
        cost *= 1 - SPOT_DISCOUNT
    if rightsizing:
        cost *= 1 - RIGHTSIZING_SAVINGS
    return {
        "replicas": replicas,
        "vcpu_hours": round(vcpu_hours, 1),
        "monthly_compute_usd": round(cost, 2),
        "spot": spot,
        "rightsizing": rightsizing,
    }


def compare_same_capacity(peak_replicas: int) -> dict:
    """Compare on-demand vs spot+rightsizing at the same peak capacity."""
    baseline = monthly_compute_cost(peak_replicas)
    optimized = monthly_compute_cost(peak_replicas, spot=True, rightsizing=True)
    savings_pct = (
        (baseline["monthly_compute_usd"] - optimized["monthly_compute_usd"])
        / baseline["monthly_compute_usd"]
        * 100
    )
    return {
        "peak_replicas": peak_replicas,
        "baseline_on_demand": baseline,
        "optimized_spot_rightsizing": optimized,
        "savings_percent": round(savings_pct, 1),
        "meets_60pct_target": savings_pct >= 60.0,
    }


def compare_autoscaling() -> dict:
    """Compare fixed baseline replicas vs autoscaling average + spot."""
    baseline = monthly_compute_cost(BASELINE_REPLICAS)
    optimized = monthly_compute_cost(AVG_REPLICAS_OPTIMIZED, spot=True, rightsizing=True)
    savings_pct = (
        (baseline["monthly_compute_usd"] - optimized["monthly_compute_usd"])
        / baseline["monthly_compute_usd"]
        * 100
    )
    return {
        "baseline_fixed_on_demand": baseline,
        "optimized_autoscale_avg": optimized,
        "peak_replicas_capacity": PEAK_REPLICAS,
        "savings_percent": round(savings_pct, 1),
        "meets_60pct_target": savings_pct >= 60.0,
        "cost_per_request_usd": round(
            optimized["monthly_compute_usd"] / REQUESTS_PER_MONTH, 8
        ),
        "requests_per_month": REQUESTS_PER_MONTH,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", action="store_true", help="Show fixed baseline only")
    parser.add_argument("--replicas", type=int, default=PEAK_REPLICAS)
    parser.add_argument("--spot", action="store_true")
    parser.add_argument("--rightsizing", action="store_true")
    parser.add_argument(
        "--mode",
        choices=["capacity", "autoscale"],
        default="capacity",
        help="capacity: same peak replicas; autoscale: fixed vs avg+spot",
    )
    args = parser.parse_args()

    if args.baseline:
        result = {"baseline_on_demand": monthly_compute_cost(BASELINE_REPLICAS)}
    elif args.spot and args.rightsizing:
        if args.mode == "autoscale":
            result = compare_autoscaling()
        else:
            result = compare_same_capacity(args.replicas)
            result["cost_per_request_usd"] = round(
                result["optimized_spot_rightsizing"]["monthly_compute_usd"]
                / REQUESTS_PER_MONTH,
                8,
            )
            result["requests_per_month"] = REQUESTS_PER_MONTH
    else:
        result = {
            "scenario": monthly_compute_cost(args.replicas),
            "hint": "Use --spot --rightsizing for optimized comparison",
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()