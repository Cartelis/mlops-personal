"""Week 3 CUDA container smoke service (not a trained fraud predictor).

Requires a Linux x86_64 NVIDIA host with a compatible driver and Container
Toolkit. Apple Silicon/MPS and CPU-only hosts deliberately fail this check.
Every health request runs and verifies a CUDA calculation in this process.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


def cuda_probe() -> dict[str, Any]:
    import torch

    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is required: use Linux x86_64, an NVIDIA GPU/driver, "
            "NVIDIA Container Toolkit and docker run --gpus all. "
            "Apple Silicon and CPU-only hosts cannot run this GPU exercise."
        )
    with torch.inference_mode():
        left = torch.tensor([[1.0, 2.0], [3.0, 4.0]], device="cuda")
        right = torch.tensor([[5.0, 6.0], [7.0, 8.0]], device="cuda")
        result = left @ right
        expected = torch.tensor([[19.0, 22.0], [43.0, 50.0]], device="cuda")
        torch.cuda.synchronize()
        if not result.is_cuda or not torch.equal(result, expected):
            raise RuntimeError("CUDA matrix multiplication produced an incorrect result")
        values = result.cpu().tolist()
    return {
        "status": "ok",
        "backend": "cuda",
        "device": torch.cuda.get_device_name(0),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "calculation": "matrix_multiplication",
        "result": values,
        "purpose": "GPU runtime verification; not fraud model inference",
    }


class GPUHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_json(404, {"detail": "Only GET /health is supported"})
            return
        try:
            self.send_json(200, cuda_probe())
        except Exception as exc:    # noqa: BLE001
            self.send_json(503, {"status": "error", "detail": str(exc)})

    def send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Run one CUDA calculation and exit")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    try:
        result = cuda_probe()
    except Exception as exc:
        raise SystemExit(f"GPU verification failed: {exc}") from exc
    print(json.dumps(result), flush=True)
    if args.check:
        return
    with HTTPServer((args.host, args.port), GPUHealthHandler) as server:
        print(f"GPU health service listening on {server.server_address[0]}:{server.server_address[1]}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
