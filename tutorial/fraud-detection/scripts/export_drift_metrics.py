"""Expose drift PSI as Prometheus metrics on :9101 for alerting demos."""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from observability.evidently_report import build_report

DRIFT_REPORT = ROOT / "docs/drift-report.json"


def load_psi() -> float:
    if DRIFT_REPORT.exists():
        data = json.loads(DRIFT_REPORT.read_text())
        return float(data.get("max_psi", 0))
    return float(build_report().get("max_psi", 0))


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return
        psi = load_psi()
        body = (
            "# HELP fraud_drift_psi Population stability index for primary feature\n"
            "# TYPE fraud_drift_psi gauge\n"
            f"fraud_drift_psi {psi}\n"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=9101)
    args = parser.parse_args()
    DRIFT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    DRIFT_REPORT.write_text(json.dumps(build_report(), indent=2), encoding="utf-8")
    server = HTTPServer(("0.0.0.0", args.port), MetricsHandler)
    print(f"Drift metrics exporter on :{args.port}/metrics (psi={load_psi()})")
    server.serve_forever()


if __name__ == "__main__":
    main()