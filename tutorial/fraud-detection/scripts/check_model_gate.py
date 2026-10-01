"""Exit 0 if model metrics pass threshold; else exit 1."""
import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", default="metrics.json")
    parser.add_argument("--threshold", type=float, default=0.95)
    parser.add_argument("--metric", default="accuracy")
    args = parser.parse_args()

    with open(args.metrics) as f:
        data = json.load(f)
    value = data.get(args.metric)
    if value is None:
        print(f"Missing metric: {args.metric}")
        sys.exit(1)
    if value < args.threshold:
        print(f"FAIL: {args.metric}={value:.4f} < {args.threshold}")
        sys.exit(1)
    print(f"PASS: {args.metric}={value:.4f} >= {args.threshold}")
    sys.exit(0)


if __name__ == "__main__":
    main()