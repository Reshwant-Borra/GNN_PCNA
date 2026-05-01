"""
Training loop for CrypticGNN.
Pre-train on CryptoSite, fine-tune on PCNA (8GLA labels).
"""
from __future__ import annotations
import argparse
from pathlib import Path

import torch
from torch_geometric.loader import DataLoader

from src.models import CrypticGNN
from .loss import focal_loss
from .dataset import PocketDataset


def train_epoch(model: CrypticGNN, loader: DataLoader, optimizer: torch.optim.Optimizer, device: str) -> float:
    """Run one training epoch. Returns mean loss."""
    model.train()
    total_loss = 0.0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        scores = model(batch.x, batch.edge_index, batch.edge_attr)
        loss = focal_loss(scores, batch.y.float())
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)


@torch.no_grad()
def eval_epoch(model: CrypticGNN, loader: DataLoader, device: str) -> dict:
    """Evaluate on loader. Returns dict with loss and AUROC."""
    raise NotImplementedError


def main(args: argparse.Namespace) -> None:
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    train_set = PocketDataset(args.train_dir)
    val_set   = PocketDataset(args.val_dir)
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True)
    val_loader   = DataLoader(val_set,   batch_size=args.batch_size)

    model = CrypticGNN().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val_loss = float('inf')
    patience_counter = 0

    for epoch in range(1, args.epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, device)
        val_metrics = eval_epoch(model, val_loader, device)
        scheduler.step()

        print(f"Epoch {epoch:03d} | train_loss={train_loss:.4f} | val_loss={val_metrics['loss']:.4f} | AUROC={val_metrics['auroc']:.4f}")

        if val_metrics['loss'] < best_val_loss:
            best_val_loss = val_metrics['loss']
            patience_counter = 0
            torch.save(model.state_dict(), Path(args.checkpoint_dir) / 'best.ckpt')
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"Early stopping at epoch {epoch}")
                break


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--train_dir', required=True)
    parser.add_argument('--val_dir', required=True)
    parser.add_argument('--checkpoint_dir', default='checkpoints/')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--patience', type=int, default=10)
    main(parser.parse_args())
