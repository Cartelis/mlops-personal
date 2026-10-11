"""GPU inference baseline for fraud-like tabular model."""
import argparse
import time

import torch
from torch import nn


class FraudNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(10, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def load_model(device: torch.device) -> FraudNet:
    model = FraudNet().to(device)
    model.eval()
    return model


@torch.no_grad()
def run_inference(model: FraudNet, batch: torch.Tensor, device: torch.device) -> torch.Tensor:
    return model(batch.to(device))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=200)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("CUDA required for week 8 GPU lab")

    device = torch.device("cuda")
    model = load_model(device)
    batch = torch.randn(args.batch_size, 10)

    for _ in range(20):
        run_inference(model, batch, device)
    torch.cuda.synchronize()

    t0 = time.perf_counter()
    for _ in range(args.iterations):
        run_inference(model, batch, device)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - t0
    ips = args.iterations * args.batch_size / elapsed
    print(f"baseline fp32 batch={args.batch_size} ips={ips:.1f}")


if __name__ == "__main__":
    main()