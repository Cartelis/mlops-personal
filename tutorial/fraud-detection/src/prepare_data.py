"""Prepare train/test split. Run: python src/prepare_data.py"""
import os

import pandas as pd
from sklearn.model_selection import train_test_split

RAW = "data/raw/dataset.csv"
OUT_DIR = "data/processed"
TEST_SIZE = 0.2
SEED = 42


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.read_csv(RAW)
    train, test = train_test_split(
        df, test_size=TEST_SIZE, random_state=SEED, stratify=df["target"]
    )
    train.to_csv(f"{OUT_DIR}/train.csv", index=False)
    test.to_csv(f"{OUT_DIR}/test.csv", index=False)
    print(f"Train: {len(train)}, Test: {len(test)}")


if __name__ == "__main__":
    main()