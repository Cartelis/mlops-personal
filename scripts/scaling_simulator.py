"""Simulate HPA/KEDA replica recommendations from target RPS (local lab demo)."""
from __future__ import annotations

import argparse
import json
import math

TARGET_RPS_PER_REPLICA = 25.0
MIN_REPLICAS = 1
MAX_REPLICAS = 50
CPU_SCALE_THRESHOLD = 0.70


def recommend_replicas(rps: float, cpu_util: float | None = None) -> dict:
    rps_based = math.ceil(rps / TARGET_RPS_PER_REPLICA) if rps > 0 else MIN_REPLICAS
    cpu_based = MIN_REPLICAS
    if cpu_util is not None and cpu_util > CPU_SCALE_THRESHOLD:
        cpu_based = math.ceil(rps_based * (cpu_util / CPU_SCALE_THRESHOLD))

    recommended = max(rps_based, cpu_based)
    recommended = max(MIN_REPLICAS, min(MAX_REPLICAS, recommended))

    return {
        "input_rps": rps,
        "input_cpu_util": cpu_util,
        "target_rps_per_replica": TARGET_RPS_PER_REPLICA,
        "recommended_replicas": recommended,
        "min_replicas": MIN_REPLICAS,
        "max_replicas": MAX_REPLICAS,
        "at_cap": recommended >= MAX_REPLICAS,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rps", type=float, required=True)
    parser.add_argument("--cpu-util", type=float, default=None)
    args = parser.parse_args()
    result = recommend_replicas(args.rps, args.cpu_util)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()