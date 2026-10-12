"""Minimal PyTorch DDP training for week 5 HPC lab."""
import argparse
import os
import time

import torch
import torch.distributed as dist
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, TensorDataset


def setup() -> int:
    dist.init_process_group("nccl")
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    torch.cuda.set_device(local_rank)
    return local_rank


def cleanup() -> None:
    dist.destroy_process_group()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    local_rank = setup()
    device = torch.device("cuda", local_rank)

    n = 10000
    x = torch.randn(n, 10)
    y = ((x[:, 0] + x[:, 1]) > 0).float().unsqueeze(1)
    dataset = TensorDataset(x, y)
    sampler = torch.utils.data.distributed.DistributedSampler(dataset)
    loader = DataLoader(dataset, batch_size=args.batch_size, sampler=sampler)

    model = nn.Sequential(
        nn.Linear(10, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid()
    )
    model = model.to(device)
    model = DDP(model, device_ids=[local_rank])
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.BCELoss()

    t0 = time.time()
    for epoch in range(args.epochs):
        sampler.set_epoch(epoch)
        total_loss = 0.0
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            opt.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()
            total_loss += loss.item()
        if local_rank == 0:
            print(f"epoch={epoch + 1} loss={total_loss / len(loader):.4f}")

    if local_rank == 0:
        elapsed = time.time() - t0
        print(
            f"DDP training done in {elapsed:.1f}s, "
            f"world_size={dist.get_world_size()}"
        )
    cleanup()


if __name__ == "__main__":
    main()