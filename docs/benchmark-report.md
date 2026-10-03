# Inference Benchmark - Week 7

## Setup

- GPU: NVIDIA A100 40GB (HPC) / T4 (fallback)
- Models:
  - Fraud ONNX via KServe (CPU)
  - LLM: TinyLlama-1.1B (demo) or Llama-2-7B (production target)
- Prompts: 50 fixed prompts, `max_tokens=64`

## Commands

```bash
python scripts/benchmark_vllm.py \
  --url http://localhost:8000 \
  --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --precision fp16 \
  --output docs/benchmark-fp16.json

python scripts/benchmark_vllm.py \
  --url http://localhost:8000 \
  --model TheBloke/TinyLlama-1.1B-Chat-v1.0-AWQ \
  --precision int4-awq \
  --output docs/benchmark-int4.json
```

## Results

| Precision | p50 (ms) | p95 (ms) | tok/s | VRAM (GB) | cost/1K tok |
|-----------|----------|----------|-------|-----------|-------------|
| FP16      |          |          |       |           |             |
| INT4 AWQ  |          |          |       |           |             |

## KServe fraud API (tabular)

| Endpoint | p95 (ms) | Notes |
|----------|----------|-------|
| fraud-detector ONNX | | target <= 80 ms |

## Decision

We deploy INT4 in production because: _(team rationale — latency, cost, quality)_

## 7B production target

For Llama-2-7B AWQ on HPC: target >= 150 tok/s (NFR-28).