"""Ask the deployed model service for one prediction - the pipeline's last step and your own check.

  python scripts/smoke_test_api.py --url http://fraud-api.mlops.svc/predict      # inside the cluster
  python scripts/smoke_test_api.py --url http://localhost:8088/predict           # via port-forward

Sends the first row of data/processed/test.csv if it exists, otherwise a built-in transaction;
exits non-zero unless the service answers 200 with a prediction in {0, 1}.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FALLBACK = {f"f{i}": v for i, v in enumerate([1.2, 0.8, -0.3, 0.1, 0.0, -1.1, 0.4, 0.2, -0.5, 0.9])}


def sample_row() -> tuple[dict, int | None]:
    test = ROOT / "data/processed/test.csv"
    if test.exists():
        with test.open() as f:
            row = next(csv.DictReader(f))
        return {k: float(v) for k, v in row.items() if k != "target"}, int(float(row["target"]))
    return FALLBACK, None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://fraud-api.mlops.svc/predict")
    parser.add_argument("--retries", type=int, default=12, help="the service may still be rolling out")
    parser.add_argument("--result", help="write the answer as JSON here (XCom)")
    args = parser.parse_args()

    features, label = sample_row()
    body = json.dumps(features).encode()
    req = urllib.request.Request(args.url, data=body, headers={"Content-Type": "application/json"})
    last = None
    for attempt in range(1, args.retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                answer = json.loads(resp.read())
            break
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last = exc
            print(f"attempt {attempt}: {exc} - waiting 5 s", flush=True)
            time.sleep(5)
    else:
        sys.exit(f"service did not answer after {args.retries} attempts: {last}")

    pred = answer.get("prediction")
    print(f"request:  {features}\nresponse: {answer}" + (f"\nlabel in test.csv: {label}" if label is not None else ""))
    if pred not in (0, 1):
        sys.exit("unexpected answer")
    if args.result:
        Path(args.result).parent.mkdir(parents=True, exist_ok=True)
        Path(args.result).write_text(json.dumps({"prediction": pred, "label": label, "url": args.url}) + "\n")


if __name__ == "__main__":
    main()
