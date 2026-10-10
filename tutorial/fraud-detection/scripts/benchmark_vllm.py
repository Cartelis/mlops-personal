"""Benchmark vLLM OpenAI-compatible endpoint: latency and throughput."""
import argparse
import json
import statistics
import time

import httpx

DEFAULT_PROMPTS = [
    "Explain MLOps in one paragraph.",
    "What is model drift?",
    "Define Kubernetes for ML workloads.",
    "How does quantization reduce VRAM?",
    "List three inference optimization techniques.",
] * 10  # 50 prompts


def run_benchmark(
    url: str,
    model: str,
    prompts: list[str],
    max_tokens: int = 64,
) -> dict:
    latencies: list[float] = []
    total_tokens = 0
    errors = 0
    base = url.rstrip("/")

    wall_start = time.time()
    with httpx.Client(timeout=120.0) as client:
        for prompt in prompts:
            start = time.time()
            try:
                response = client.post(
                    f"{base}/v1/completions",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                latencies.append(time.time() - start)
                usage = payload.get("usage", {})
                total_tokens += usage.get("total_tokens", max_tokens)
            except httpx.HTTPError:
                errors += 1
    elapsed = time.time() - wall_start

    if not latencies:
        return {"error": "all requests failed", "errors": errors}

    sorted_lat = sorted(latencies)
    p95_idx = min(int(len(sorted_lat) * 0.95), len(sorted_lat) - 1)
    return {
        "model": model,
        "requests": len(prompts),
        "errors": errors,
        "p50_ms": round(statistics.median(latencies) * 1000, 2),
        "p95_ms": round(sorted_lat[p95_idx] * 1000, 2),
        "total_tokens": total_tokens,
        "elapsed_sec": round(elapsed, 2),
        "tokens_per_sec": round(total_tokens / elapsed, 2) if elapsed else 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--model", required=True)
    parser.add_argument("--precision", default="fp16")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--output", required=True)
    parser.add_argument("--prompts", type=int, default=50)
    args = parser.parse_args()

    prompts = DEFAULT_PROMPTS[: args.prompts]
    result = run_benchmark(args.url, args.model, prompts, args.max_tokens)
    result["precision"] = args.precision

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()