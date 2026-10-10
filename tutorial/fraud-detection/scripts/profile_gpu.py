"""Profile GPU inference with PyTorch Profiler."""
import argparse
from pathlib import Path

import torch
from torch.profiler import ProfilerActivity, profile, schedule

from src.inference_gpu import FraudNet, run_inference


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output", default="docs/torch_profiler_trace.json")
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("CUDA required for week 8 GPU lab")

    device = torch.device("cuda")
    model = FraudNet().to(device).eval()
    batch = torch.randn(args.batch_size, 10)

    with profile(
        activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
        schedule=schedule(wait=1, warmup=1, active=3, repeat=1),
        record_shapes=True,
        profile_memory=True,
    ) as prof:
        for _ in range(5):
            run_inference(model, batch, device)
            prof.step()

    print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=12))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    prof.export_chrome_trace(str(output))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()