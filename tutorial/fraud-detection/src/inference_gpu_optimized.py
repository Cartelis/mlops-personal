"""Optimized GPU inference with AMP and optional torch.compile."""
import torch

from src.inference_gpu import FraudNet


@torch.no_grad()
def run_inference_amp(
    model: FraudNet, batch: torch.Tensor, device: torch.device
) -> torch.Tensor:
    with torch.autocast(device_type="cuda", dtype=torch.float16):
        return model(batch.to(device))


def maybe_compile(model: FraudNet) -> FraudNet:
    if hasattr(torch, "compile"):
        return torch.compile(model)
    return model