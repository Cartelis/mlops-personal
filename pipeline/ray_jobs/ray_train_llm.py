"""Week-2's Qwen3-0.6B fine-tuning loop inside Ray Train - distribution added around the same loop.

Week 2 (tutorial/wb_monitoring/finetune_qwen.py) took chapter 8 of Sebastian Raschka's *Build a
Reasoning Model (From Scratch)* and added monitoring (W&B) around the training loop. This script
takes that loop and adds *distribution*: the loop body is the same, but it runs as `train_func`
on every Ray Train worker, with the model wrapped by `prepare_model` and the examples sharded by
worker rank. What changes between one GPU and many is ONE line - the ScalingConfig (see main()).

Minimal compute on purpose (as in week 2's smoke run): the defaults train on 40 examples and
take a few minutes on one GPU. The principle, not the loss curve, is the point.

  python pipeline/ray_jobs/ray_train_llm.py --gpu                              # 1 worker, 1 GPU
  python pipeline/ray_jobs/ray_train_llm.py --num-workers 2 --no-gpu --train-size 4 --max-seq-len 384
                                                                              # CPU smoke: 2 workers, data sharded
  python pipeline/ray_jobs/ray_train_llm.py --gpu --num-workers 8             # the one-line change (8 GPUs)
"""
from __future__ import annotations

import argparse
import os
import random
import time

import ray
import ray.train
import ray.train.torch
import torch
from ray.train import RunConfig, ScalingConfig
from ray.train.torch import TorchTrainer


def train_func(config: dict) -> None:
    """Runs once per worker. Everything inside is week 2's loop, plus the four Ray Train lines."""
    from reasoning_from_scratch.ch03 import load_model_and_tokenizer
    from reasoning_from_scratch.ch08 import (
        build_examples, compute_example_loss, evaluate_examples, filter_examples_by_max_len,
        load_distill_data, load_reasoning_tokenizer, save_checkpoint,
    )

    ctx = ray.train.get_context()
    rank, world = ctx.get_world_rank(), ctx.get_world_size()      # Ray Train line 1: who am I
    device = ray.train.torch.get_device()                           # Ray Train line 2: my device
    os.chdir(config["data_dir"])                                    # the book caches model + data in cwd
    torch.manual_seed(config["seed"])

    # --- data: the book's chapter-8 pipeline, unchanged ---------------------------------------
    raw = load_distill_data(partition="deepseek-r1-math-train")
    tokenizer = load_reasoning_tokenizer()
    examples, _ = build_examples(raw, tokenizer)
    examples = filter_examples_by_max_len(examples, max_len=config["max_seq_len"])
    rng = random.Random(config["seed"])
    rng.shuffle(examples)
    val_examples = examples[: config["val_size"]]
    train_examples = examples[config["val_size"]: config["val_size"] + config["train_size"]]
    my_examples = train_examples[rank::world]                       # Ray Train line 3: my shard of the data

    # --- model: loaded by every worker, wrapped once --------------------------------------------
    model, _ = load_model_and_tokenizer(which_model="base", device=device, use_compile=False)
    model = ray.train.torch.prepare_model(model)                    # Ray Train line 4: device + DDP when world > 1
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["lr"])

    run = None
    if rank == 0 and config["wandb"]:                               # tracking only from rank 0 (Train V2 pattern)
        import wandb
        run = wandb.init(project=config["project"], config={**config, "world_size": world})

    # --- the book's training loop (listing 8.13), per worker -----------------------------------
    model.train()
    step, t_start = 0, time.time()
    total = config["epochs"] * len(my_examples)
    for epoch in range(1, config["epochs"] + 1):
        rng.shuffle(my_examples)
        for example in my_examples:
            step += 1
            t0 = time.time()
            optimizer.zero_grad()
            loss = compute_example_loss(model, example, device)
            loss.backward()                                         # DDP all-reduces the gradients here
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), config["grad_clip"])
            optimizer.step()
            metrics = {"train/loss": loss.item(), "train/grad_norm": float(grad_norm),
                       "perf/step_time_s": time.time() - t0, "rank": rank, "step": step}
            if step % config["log_every"] == 0 or step == total:
                raw_model = model.module if hasattr(model, "module") else model
                metrics["val/loss"] = evaluate_examples(model=raw_model, examples=val_examples, device=device)
                model.train()
                print(f"[rank {rank}] step {step}/{total} train_loss={loss.item():.4f} val_loss={metrics['val/loss']:.4f}", flush=True)
            if run is not None:
                run.log(metrics, step=step)
            ray.train.report(metrics)                               # the trainer collects this from every worker
        if rank == 0:
            raw_model = model.module if hasattr(model, "module") else model
            path = save_checkpoint(model=raw_model, checkpoint_dir=config["checkpoint_dir"], step=step, suffix=f"epoch{epoch}")
            print(f"[rank 0] checkpoint: {path}", flush=True)

    if run is not None:
        run.summary["train/total_minutes"] = (time.time() - t_start) / 60
        run.finish()
    print(f"[rank {rank}] done: {step} steps on {len(my_examples)} examples in {(time.time() - t_start) / 60:.1f} min", flush=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--num-workers", type=int, default=1, help="Ray Train workers (= GPUs when --gpu)")
    p.add_argument("--gpu", dest="gpu", action="store_true", default=True)
    p.add_argument("--no-gpu", dest="gpu", action="store_false", help="CPU workers (smoke test)")
    p.add_argument("--train-size", type=int, default=40, help="examples in total, sharded over the workers")
    p.add_argument("--val-size", type=int, default=8)
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--lr", type=float, default=5e-6)
    p.add_argument("--max-seq-len", type=int, default=1024)
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--log-every", type=int, default=10)
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--data-dir", default=os.environ.get("LLM_CACHE_DIR", os.getcwd()),
                   help="where qwen3/ and the dataset JSON are (or get downloaded)")
    p.add_argument("--checkpoint-dir", default="checkpoints")
    p.add_argument("--storage-path", default=os.environ.get("RAY_STORAGE_PATH", "/tmp/ray_results"),
                   help="Ray Train run directory; must be shared storage for multi-node runs")
    p.add_argument("--project", default="mlops-w9-ray-train")
    p.add_argument("--no-wandb", action="store_true")
    p.add_argument("--address", default=os.environ.get("RAY_ADDRESS"), help="Ray cluster (default: local)")
    args = p.parse_args()

    ray.init(address=args.address) if args.address else ray.init()
    print("Ray resources:", ray.cluster_resources(), flush=True)

    config = {k: v for k, v in vars(args).items() if k not in ("num_workers", "gpu", "address", "storage_path")}
    config["wandb"] = not args.no_wandb and bool(os.environ.get("WANDB_API_KEY") or os.environ.get("WANDB_MODE"))

    trainer = TorchTrainer(
        train_func,
        train_loop_config=config,
        # ---- THE line. 1 GPU: num_workers=1. 8 GPUs of one node: num_workers=8. 16 GPUs on two nodes:
        # num_workers=16 and a storage_path every node can reach (NFS, S3). Nothing in train_func changes.
        scaling_config=ScalingConfig(num_workers=args.num_workers, use_gpu=args.gpu),
        run_config=RunConfig(name="qwen3-distill", storage_path=args.storage_path),
    )
    result = trainer.fit()
    print("training finished; last reported metrics:", result.metrics or "see the worker log above / W&B", flush=True)
    print("checkpoint dir:", os.path.join(args.data_dir, args.checkpoint_dir), flush=True)


if __name__ == "__main__":
    main()
