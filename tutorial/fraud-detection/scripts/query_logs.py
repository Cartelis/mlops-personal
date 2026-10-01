"""Query structured JSON logs from stdin or file for root-cause demo."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observability.log_analyzer import analyze_file, analyze_stream


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Log file path (default: stdin)")
    parser.add_argument("--slow-ms", type=float, default=80.0)
    parser.add_argument("--last", type=int, default=200)
    args = parser.parse_args()

    if args.file:
        summary = analyze_file(Path(args.file), slow_ms=args.slow_ms, last=args.last)
    else:
        summary = analyze_stream(sys.stdin, slow_ms=args.slow_ms, last=args.last)

    print(json.dumps({
        "total_records": summary.total,
        "errors": summary.errors,
        "slow_requests": summary.slow_requests,
        "p95_duration_ms": summary.p95_duration_ms,
        "slow_threshold_ms": args.slow_ms,
    }, indent=2))


if __name__ == "__main__":
    main()