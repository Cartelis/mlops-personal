"""Benchmark GPU inference: latency percentiles and throughput."""
import argparse
import json
import statistics
import time

import torch

from src.inference_gpu import FraudNet, run_inference
from src.inference_gpu_optimized import maybe_compile, run_inference_amp


def benchmark(
    fn,
    model: FraudNet,
    batch: torch.Tensor,
    device: torch.device,
    iterations: int = 200,
    warmup: int = 20,
) -> dict:
    for _ in range(warmup):
        fn(model, batch, device)
    torch.cuda.synchronize()

    latencies: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn(model, batch, device)
        torch.cuda.synchronize()
        latencies.append(time.perf_counter() - t0)

    sorted_lat = sorted(latencies)
    p95_idx = min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)
    total = sum(latencies)
    return {
        "p50_ms": round(statistics.median(latencies) * 1000, 4),
        "p95_ms": round(sorted_lat[p95_idx] * 1000, 4),
        "throughput_ips": round((iterations * batch.size(0)) / total, 2),
        "iterations": iterations,
        "batch_size": batch.size(0),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--precision", choices=["fp32", "amp"], default="fp32")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--compile", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("CUDA required for week 8 GPU lab")

    device = torch.device("cuda")
    model = FraudNet().to(device).eval()
    if args.compile:
        model = maybe_compile(model)

    batch = torch.randn(args.batch_size, 10)
    fn = run_inference if args.precision == "fp32" else run_inference_amp

    result = benchmark(fn, model, batch, device, iterations=args.iterations)
    result.update(
        {
            "precision": args.precision,
            "compiled": args.compile,
            "gpu": torch.cuda.get_device_name(0),
        }
    )

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()