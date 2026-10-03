"""Run headless Locust load test against fraud API."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="http://127.0.0.1:8080")
    parser.add_argument("--users", type=int, default=50)
    parser.add_argument("--spawn-rate", type=int, default=10)
    parser.add_argument("--run-time", default="2m")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prefix = OUT_DIR / "locust"

    cmd = [
        sys.executable, "-m", "locust",
        "-f", str(ROOT / "scaling" / "locustfile.py"),
        "--headless",
        "-u", str(args.users),
        "-r", str(args.spawn_rate),
        "--run-time", args.run_time,
        "--host", args.host,
        "--csv", str(prefix),
        "--html", str(OUT_DIR / "locust-report.html"),
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)
    print(f"Reports written to {OUT_DIR}/locust-*")


if __name__ == "__main__":
    main()