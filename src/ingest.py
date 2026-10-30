"""Ingest step of the orchestrated pipeline: fetch "today's transactions" into data/raw/dataset.csv.

The course has no real feed, so the same synthetic generator as scripts/bootstrap.py runs here
(seed 42, 1000 rows x 10 features -> the file is byte-identical on every machine, and its md5 is the
one DVC recorded in week 2). It prints that md5 so the run can be traced to the data version.

  python src/ingest.py                 # the standard course dataset
  python src/ingest.py --seed 43       # "a new day of data" - different hash, different model
"""
import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/dataset.csv"
N_SAMPLES, N_FEATURES = 1000, 10


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--rows", type=int, default=N_SAMPLES)
    parser.add_argument("--force", action="store_true", help="overwrite an existing file")
    args = parser.parse_args()

    if RAW.exists() and not args.force and args.seed == 42 and args.rows == N_SAMPLES:
        print(f"{RAW.relative_to(ROOT)} exists - keeping it (idempotent); md5={hashlib.md5(RAW.read_bytes()).hexdigest()}")
        return
    rng = np.random.default_rng(args.seed)
    x = rng.standard_normal((args.rows, N_FEATURES))
    y = ((x[:, 0] + x[:, 1]) > 0).astype(int)
    df = pd.DataFrame(x, columns=[f"f{i}" for i in range(N_FEATURES)])
    df["target"] = y
    RAW.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW, index=False)
    print(f"wrote {RAW.relative_to(ROOT)} ({len(df)} rows, seed {args.seed}); md5={hashlib.md5(RAW.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
