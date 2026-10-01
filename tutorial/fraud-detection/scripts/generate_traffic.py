"""Generate inference traffic against local fraud API for observability demos."""
from __future__ import annotations

import argparse
import random
import time

import httpx

PAYLOAD = {f"f{i}": round(random.uniform(-1, 1), 3) for i in range(10)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8080")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--slow-fraction", type=float, default=0.0,
                          help="Fraction of requests with artificial client-side delay")
    args = parser.parse_args()

    ok = 0
    with httpx.Client(timeout=10.0) as client:
        for i in range(args.requests):
            if random.random() < args.slow_fraction:
                time.sleep(0.15)
            payload = {k: round(random.uniform(-2, 2), 3) for k in PAYLOAD}
            try:
                resp = client.post(f"{args.url}/predict", json=payload)
                if resp.status_code == 200:
                    ok += 1
            except httpx.HTTPError:
                pass
            time.sleep(0.01)
    print(f"Completed {args.requests} requests, ok={ok}")


if __name__ == "__main__":
    main()