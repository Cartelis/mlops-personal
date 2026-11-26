"""Week 13 demo D0 - model extraction through the public /predict API.

The "threat actor" only has what any client has: the URL of /predict.
  1. send N synthetic payments (random feature vectors) and record every answer;
  2. train a surrogate model on the (input -> answer) pairs;
  3. measure how often the surrogate answers like our real model.

Agreement is measured on data/processed/test.csv - real held-out payments the attacker never saw -
by asking the real API and the stolen copy the same questions.

Run (fraud API must be up, e.g. `python -m uvicorn src.serve:app --port 8080`):
    python security/demos/extract_model.py --url http://localhost:8080/predict --queries 5000
Lecture use: start it at the beginning, reveal the final line later (slide "Grįžkime prie pradžios").
Only standard library + numpy/pandas/scikit-learn (already in the project requirements).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parents[2]
FEATURES = [f"f{i}" for i in range(10)]


def ask(url: str, row: np.ndarray) -> int:
    body = json.dumps({f: float(v) for f, v in zip(FEATURES, row)}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return int(json.load(resp)["prediction"])


def ask_many(url: str, X: np.ndarray, workers: int, label: str) -> np.ndarray:
    out = np.empty(len(X), dtype=int)
    done = 0
    step = max(len(X) // 10, 1)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, y in enumerate(pool.map(lambda r: ask(url, r), X)):
            out[i] = y
            done += 1
            if done % step == 0 or done == len(X):
                print(f"  {label}: {done}/{len(X)} answers", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://localhost:8080/predict")
    ap.add_argument("--queries", type=int, default=5000, help="how many synthetic payments to send")
    ap.add_argument("--workers", type=int, default=8, help="parallel requests")
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--test-csv", default=str(ROOT / "data/processed/test.csv"))
    ap.add_argument("--out", default="", help="optional JSON file with the final numbers")
    args = ap.parse_args()

    try:
        ask(args.url, np.zeros(len(FEATURES)))
    except (urllib.error.URLError, OSError, KeyError) as exc:
        print(f"Cannot reach {args.url}: {exc}\nStart the API first: python -m uvicorn src.serve:app --port 8080")
        return 1

    rng = np.random.default_rng(args.seed)
    t0 = time.time()

    print(f"[1/3] Recon: sending {args.queries} synthetic payments to {args.url} ...", flush=True)
    X_q = rng.normal(0.0, 1.0, size=(args.queries, len(FEATURES)))
    y_q = ask_many(args.url, X_q, args.workers, "queries")
    print(f"      fraud answers: {y_q.mean():.0%} of queries", flush=True)

    print("[2/3] Training the stolen copy (surrogate) on the API's answers ...", flush=True)
    copy = RandomForestClassifier(n_estimators=200, random_state=args.seed, n_jobs=-1)
    copy.fit(pd.DataFrame(X_q, columns=FEATURES), y_q)

    print("[3/3] Comparing copy vs real model on held-out real payments ...", flush=True)
    test = pd.read_csv(args.test_csv)
    X_t = test[FEATURES].to_numpy()
    y_real = ask_many(args.url, X_t, args.workers, "real model")
    y_copy = copy.predict(pd.DataFrame(X_t, columns=FEATURES))
    agree = float((y_copy == y_real).mean())
    majority = float(max(y_real.mean(), 1 - y_real.mean()))   # what "always guess the common answer" would get
    elapsed = time.time() - t0

    print()
    print("=" * 64)
    print(f"  Queries sent to /predict : {args.queries}")
    print(f"  Time                     : {elapsed:.0f} s")
    print(f"  Cluster access used      : none (public API only)")
    print(f"  Agreement with our model : {agree:.1%}  on {len(X_t)} real test payments")
    print(f"  (guessing the common answer would give {majority:.0%})")
    print("=" * 64)

    if args.out:
        Path(args.out).write_text(json.dumps({
            "queries": args.queries, "seconds": round(elapsed, 1), "agreement": round(agree, 4),
            "majority_baseline": round(majority, 4), "test_rows": int(len(X_t)),
        }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
