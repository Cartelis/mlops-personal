"""Fine-tune Qwen3-0.6B on DeepSeek-R1 math reasoning traces, monitored with Weights & Biases.

Recipe: chapter 8 ("distillation") of Sebastian Raschka, *Build a Reasoning Model
(From Scratch)* — https://github.com/rasbt/reasoning-from-scratch. Data preparation
and the loss come from the book's own package; this script replaces the book's
CSV logging with live W&B instrumentation, which is the point of the exercise:
the training loop is unchanged, monitoring is added around it.

Data: https://huggingface.co/datasets/rasbt/math_distill (12,000 MATH problems
answered by DeepSeek-R1 with <think> reasoning traces; ~107 MB JSON, downloaded
and cached on first run). Model: Qwen3-0.6B base (downloaded on first run).

Runs:
  python finetune_qwen.py                          # short lab run (~300 steps)
  python finetune_qwen.py --train_size 12 --val_size 4 --log_every 4   # smoke test
  WANDB_MODE=offline python finetune_qwen.py       # no account / no network for W&B
"""
import argparse
import random
import time

import torch
import wandb
from reasoning_from_scratch.ch02 import get_device
from reasoning_from_scratch.ch03 import load_model_and_tokenizer, render_prompt
from reasoning_from_scratch.ch06 import sample_response
from reasoning_from_scratch.ch08 import (
    build_examples,
    compute_example_loss,
    evaluate_examples,
    filter_examples_by_max_len,
    load_distill_data,
    load_reasoning_tokenizer,
    save_checkpoint,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train_size", type=int, default=300,
                   help="training examples (book uses all ~6.7k; 300 => a minutes-long run)")
    p.add_argument("--val_size", type=int, default=25, help="held-out examples for val loss")
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--lr", type=float, default=5e-6, help="book's value for this setup")
    p.add_argument("--schedule", choices=["constant", "cosine"], default="cosine",
                   help="book uses constant; cosine adds a warm-up + decay curve worth watching")
    p.add_argument("--warmup_frac", type=float, default=0.1)
    p.add_argument("--max_seq_len", type=int, default=1024,
                   help="filter longer examples (book: 2048 => ~15 GB VRAM; 1024 needs much less)")
    p.add_argument("--grad_clip", type=float, default=1.0)
    p.add_argument("--log_every", type=int, default=25, help="steps between val-loss evaluations")
    p.add_argument("--sample_prompt_idx", type=int, default=4,
                   help="dataset index used for the before/after generation table (-1 disables)")
    p.add_argument("--max_new_tokens", type=int, default=384, help="for the sample generations")
    p.add_argument("--seed", type=int, default=123)
    p.add_argument("--project", default="mlops-w2-wb-monitoring")
    p.add_argument("--run_name", default=None)
    p.add_argument("--watch_gradients", action="store_true",
                   help="log gradient histograms (W&B 'watch'); adds overhead")
    p.add_argument("--checkpoint_dir", default="checkpoints")
    return p.parse_args()


def generate_sample(model, tokenizer, problem: str, device, max_new_tokens: int) -> str:
    model.eval()
    with torch.no_grad():
        _, _, text = sample_response(   # returns (token_ids, prompt_len, decoded_text)
            model, tokenizer, render_prompt(problem), device,
            max_new_tokens=max_new_tokens, temperature=0.8, top_p=0.9,
        )
    model.train()
    return text


def main() -> None:
    args = parse_args()
    torch.manual_seed(args.seed)
    device = get_device()

    # --- data: the book's chapter-8 pipeline, unchanged -----------------------
    raw = load_distill_data(partition="deepseek-r1-math-train")   # cached after first download
    tokenizer = load_reasoning_tokenizer()                        # Qwen3 tokenizer with <think> tokens
    examples, skipped = build_examples(raw, tokenizer)
    examples = filter_examples_by_max_len(examples, max_len=args.max_seq_len)
    rng = random.Random(args.seed)
    rng.shuffle(examples)
    val_examples = examples[: args.val_size]
    train_examples = examples[args.val_size : args.val_size + args.train_size]

    # --- model ----------------------------------------------------------------
    model, _ = load_model_and_tokenizer(which_model="base", device=device, use_compile=False)
    total_steps = args.epochs * len(train_examples)

    # --- monitoring -----------------------------------------------------------
    run = wandb.init(
        project=args.project,
        name=args.run_name,
        config={
            **vars(args),
            "model": "qwen3-0.6B-base",
            "dataset": "rasbt/math_distill:deepseek-r1-math-train",
            "n_train": len(train_examples),
            "n_val": len(val_examples),
            "n_skipped": skipped,
            "total_steps": total_steps,
            "loss": "answer-only cross-entropy (hard distillation)",
        },
    )
    if args.watch_gradients:
        wandb.watch(model, log="gradients", log_freq=args.log_every)

    sample_problem = None
    if args.sample_prompt_idx >= 0:
        sample_problem = raw[args.sample_prompt_idx]["problem"]
        before = generate_sample(model, tokenizer, sample_problem, device, args.max_new_tokens)

    # --- optimizer (book: AdamW, constant lr; cosine schedule is our addition) -
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    if args.schedule == "cosine":
        warmup = max(1, int(total_steps * args.warmup_frac))
        scheduler = torch.optim.lr_scheduler.SequentialLR(
            optimizer,
            [
                torch.optim.lr_scheduler.LinearLR(optimizer, 0.01, 1.0, warmup),
                torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, total_steps - warmup),
            ],
            milestones=[warmup],
        )
    else:
        scheduler = None

    # --- the book's training loop (listing 8.13) + wandb.log ------------------
    model.train()
    global_step = 0
    t_start = time.time()
    for epoch in range(1, args.epochs + 1):
        epoch_examples = list(train_examples)
        rng.shuffle(epoch_examples)
        for example in epoch_examples:
            global_step += 1
            t0 = time.time()

            optimizer.zero_grad()
            loss = compute_example_loss(model, example, device)
            loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            optimizer.step()
            if scheduler is not None:
                scheduler.step()

            step_time = time.time() - t0
            n_tokens = len(example["token_ids"])
            wandb.log(
                {
                    "train/loss": loss.item(),
                    "train/grad_norm": grad_norm.item(),
                    "train/lr": optimizer.param_groups[0]["lr"],
                    "train/epoch": epoch,
                    "perf/step_time_s": step_time,
                    "perf/tokens_per_s": n_tokens / step_time,
                    "perf/seq_len": n_tokens,
                },
                step=global_step,
            )

            if global_step % args.log_every == 0 or global_step == total_steps:
                val_loss = evaluate_examples(model=model, examples=val_examples, device=device)
                model.train()
                wandb.log({"val/loss": val_loss}, step=global_step)
                print(
                    f"[Epoch {epoch}/{args.epochs} Step {global_step}/{total_steps}] "
                    f"train_loss={loss.item():.4f} val_loss={val_loss:.4f} "
                    f"lr={optimizer.param_groups[0]['lr']:.2e}"
                )

        ckpt_path = save_checkpoint(
            model=model, checkpoint_dir=args.checkpoint_dir,
            step=global_step, suffix=f"epoch{epoch}",
        )
        print(f"Saved checkpoint to {ckpt_path}")

    wandb.summary["train/total_minutes"] = (time.time() - t_start) / 60

    if sample_problem is not None:
        after = generate_sample(model, tokenizer, sample_problem, device, args.max_new_tokens)
        table = wandb.Table(columns=["problem", "before fine-tune", "after fine-tune"])
        table.add_data(sample_problem, before, after)
        wandb.log({"samples/before_after": table})

    run.finish()
    print(f"Done: {global_step} steps in {(time.time() - t_start) / 60:.1f} min")


if __name__ == "__main__":
    main()
