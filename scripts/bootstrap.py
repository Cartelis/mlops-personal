"""Generate sample data and train a baseline model for local/Docker testing."""
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

SEED = 42
N_SAMPLES = 1000
N_FEATURES = 10


def main() -> None:
    rng = np.random.default_rng(SEED)
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    x = rng.standard_normal((N_SAMPLES, N_FEATURES))
    y = ((x[:, 0] + x[:, 1]) > 0).astype(int)
    columns = [f"f{i}" for i in range(N_FEATURES)]
    df = pd.DataFrame(x, columns=columns)
    df["target"] = y
    df.to_csv("data/raw/dataset.csv", index=False)
    print(f"Wrote data/raw/dataset.csv ({len(df)} rows)")

    from sklearn.model_selection import train_test_split

    train, test = train_test_split(df, test_size=0.2, random_state=SEED, stratify=y)
    train.to_csv("data/processed/train.csv", index=False)
    test.to_csv("data/processed/test.csv", index=False)

    model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=SEED)
    model.fit(train.drop("target", axis=1), train["target"])
    joblib.dump(model, "models/model.pkl")
    print("Wrote models/model.pkl")


if __name__ == "__main__":
    main()