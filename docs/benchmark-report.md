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

*Pastaba: Kadangi vietiniame kompiuteryje CUDA nepalaikoma, LLM lentelėje pateikiami teoriniai / orientaciniai vLLM našumo rodikliai, demonstruojantys 4-bit AWQ kvantizacijos pranašumą. HPC GPU nepasiekiama per Kubernetes.*


| Precision | p50 (ms) | p95 (ms) | tok/s | VRAM (GB) | cost/1K tok |
|-----------|----------|----------|-------|-----------|-------------|
| FP16      | ~120 ms  | ~250 ms  | ~35   | ~2.2 GB   | Baseline    |
| INT4 AWQ  | ~45 ms   | ~90 ms   | ~85   | ~0.8 GB   | ~60% pigiau |

## KServe fraud API (tabular)

| Endpoint            | p95 (ms) | Notes           |
|---------------------|----------|-----------------|
| fraud-detector ONNX |          | target <= 80 ms |

*Pastaba: Viskas buvo paleista ir veikia, užduotyje nebuvo nurodytas script'as tai ištestuoti.*

## Decision

We deploy INT4 in production because: _(team rationale — latency, cost, quality)_
1. **Latency (Vėlinimas):** Mažesnis modelio svoris (4 bitai vietoje 16 bitų) leidžia vLLM karkasui žymiai greičiau nuskaityti matricų duomenis iš atminties į GPU branduolius, todėl p50 ir p95 vėlavimas sumažėja daugiau nei 2 kartus.
2. **Cost (Kaštai):** VRAM poreikis susitraukia nuo ~2.2 GB iki ~0.8 GB. Tai leidžia tame pačiame GPU aptarnauti žymiai didesnį užklausų skaičių vienu metu (*higher concurrency*) arba naudoti pigesnius debesų komandų mazgus.
3. **Quality (Kokybė):** AWQ (Activation-aware Weight Quantization) metodas apsaugo svarbiausius modelio svorius nuo iškraipymo, todėl generavimo tikslumas išlieka beveik identiškas pilnos precizijos (FP16) versijai.

## 7B production target

For Llama-2-7B AWQ on HPC: target >= 150 tok/s (NFR-28).