"""Run data contract validation and write JSON report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validation.data_contract import run_contract


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/data-validation-report.json")
    args = parser.parse_args()

    report = run_contract()
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()