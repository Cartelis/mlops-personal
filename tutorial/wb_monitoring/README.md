# wb_monitoring — LLM fine-tuning monitored with Weights & Biases

Week-2 lab extension: fine-tune **Qwen3-0.6B** on **DeepSeek-R1 math reasoning
traces** and watch the training live in W&B. The training recipe is chapter 8 of
Sebastian Raschka, *Build a Reasoning Model (From Scratch)*
(https://github.com/rasbt/reasoning-from-scratch); the exercise here is the
**monitoring**: the book logs to a CSV file — we instrument the same loop with
`wandb.init` / `wandb.log` and read the curves in the browser instead.

## Setup

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate
wandb login          # paste your API key from https://wandb.ai/authorize
                     # no account? use offline mode below
```

Requires an NVIDIA GPU (~10 GB free VRAM with the default `--max_seq_len 1024`;
use `--max_seq_len 512` on smaller cards).
First run downloads the dataset (~107 MB, from
https://huggingface.co/datasets/rasbt/math_distill) and the model (~1.5 GB);
both are cached in this directory.

## Run

```bash
python finetune_qwen.py                                       # lab run: 300 steps
python finetune_qwen.py --train_size 12 --val_size 4 --log_every 4   # 1-min smoke test
WANDB_MODE=offline python finetune_qwen.py                    # no W&B account needed;
                                                              # `wandb sync wandb/offline-run-*` later
python finetune_qwen.py --schedule constant                   # the book's original constant lr
python finetune_qwen.py --watch_gradients                     # + gradient histograms
```

## What gets logged

| Panel | Metric | What it tells you |
|---|---|---|
| `train/loss` | per-step cross-entropy (single example) | noisy by construction — compare with `val/loss` |
| `val/loss` | held-out loss every `--log_every` steps | the real training signal |
| `train/lr` | learning rate | warm-up + cosine decay (or flat with `--schedule constant`) |
| `train/grad_norm` | gradient norm before clipping | spikes = the reason `--grad_clip 1.0` exists |
| `perf/*` | step time, tokens/s, sequence length | why throughput varies with example length |
| System | GPU utilization / memory / power | collected automatically by W&B |
| `samples/before_after` | one generation before vs after | what ~300 steps of distillation actually change |

## Files

- `finetune_qwen.py` — data prep imported from the book's package
  (`reasoning_from_scratch.ch08`), training loop written out in full with W&B calls.
- `requirements.txt` — pinned versions.
- Runtime artifacts (git-ignore these): `qwen3/` (model + tokenizer),
  `deepseek-r1-math-train.json` (dataset), `checkpoints/`, `wandb/`.
