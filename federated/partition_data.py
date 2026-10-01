"""Partition training data into federated client shards."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / "data" / "processed" / "train.csv"
OUT_DIR = ROOT / "data" / "federated"


def partition(clients: int) -> dict:
    if not TRAIN.exists():
        raise FileNotFoundError(f"Missing {TRAIN}; run scripts/bootstrap.py first")

    df = pd.read_csv(TRAIN).sample(frac=1.0, random_state=42).reset_index(drop=True)
    shards = [df.iloc[i::clients].copy() for i in range(clients)]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = []
    for idx, shard in enumerate(shards):
        client_dir = OUT_DIR / f"client_{idx}"
        client_dir.mkdir(parents=True, exist_ok=True)
        path = client_dir / "train.csv"
        shard.to_csv(path, index=False)
        paths.append(str(path.relative_to(ROOT)))

    return {"clients": clients, "rows_per_client": [len(s) for s in shards], "paths": paths}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clients", type=int, default=3)
    args = parser.parse_args()
    import json

    print(json.dumps(partition(args.clients), indent=2))


if __name__ == "__main__":
    main()