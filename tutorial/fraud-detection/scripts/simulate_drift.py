"""Create drifted sample data to trigger the self-healing agent."""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
OUT = Path("data/raw/drift_sample.csv")
N = 500


def main() -> None:
    rng = np.random.default_rng(SEED)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # Shift f0 distribution to simulate covariate drift
    x = rng.normal(loc=2.0, scale=1.0, size=(N, 10))
    y = ((x[:, 0] + x[:, 1]) > 0).astype(int)
    columns = [f"f{i}" for i in range(10)]
    df = pd.DataFrame(x, columns=columns)
    df["target"] = y
    df.to_csv(OUT, index=False)
    print(f"Wrote drifted sample to {OUT} ({len(df)} rows, f0 mean shifted)")


if __name__ == "__main__":
    main()