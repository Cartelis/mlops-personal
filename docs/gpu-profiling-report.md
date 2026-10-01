# GPU Profiling Report - Week 8

## Environment

- GPU: _(e.g. NVIDIA A100 40GB)_
- CUDA: _(version)_
- PyTorch: _(version)_
- Host: University HPC

## Benchmark commands

```bash
python scripts/benchmark_gpu_inference.py --precision fp32 --batch-size 1 \
  --output docs/benchmark-gpu-fp32-b1.json
python scripts/benchmark_gpu_inference.py --precision amp --batch-size 32 \
  --output docs/benchmark-gpu-amp-b32.json
python scripts/profile_gpu.py --output docs/torch_profiler_trace.json
```

## Baseline vs optimized

| Config | batch | precision | p50 (ms) | p95 (ms) | ips | GPU util (%) |
|--------|-------|-----------|----------|----------|-----|--------------|
| baseline | 1 | fp32 | | | | |
| optimized | 32 | amp | | | | |
| tensorrt (optional) | 32 | fp16 | | | | |

## Speedup

- Throughput speedup (ips): _X.x_
- p95 latency improvement: _Y%_
- Target: >= 2x throughput (NFR-31)

## Bottleneck analysis

1. _(e.g. low GPU util at batch=1 — kernel launch overhead)_
2. _(AMP + larger batch — higher Tensor Core utilization)_

## Profiler findings

- Top CUDA ops: _(from profile_gpu.py table)_
- Trace file: `docs/torch_profiler_trace.json`

## Optimization decisions

_(What was applied and why — AMP, batch size, TensorRT, torch.compile)_