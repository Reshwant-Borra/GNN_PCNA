"""
Training loop for CrypticGNN.
Pre-train on CryptoSite, fine-tune on PCNA (8GLA labels).

eval_epoch implementation contributed by Advay (advay.awesomer@gmail.com).
"""
from __future__ import annotations
import argparse
from pathlib import Path

import torch
import numpy as np
from torch_geometric.loader import DataLoader
from sklearn.metrics import roc_auc_score

from src.models import CrypticGNN, PocketGNN
from src.models.cryptic_gnn import pocket_loss, focal_loss
from .dataset import PocketDataset


def _forward(model, batch, use_symmetry: bool = False):
    """Route forward pass for either v1 (CrypticGNN) or v2 (PocketGNN)."""
    if isinstance(model, PocketGNN):
        chain_id = getattr(batch, "chain_id", None)
        scores = model(
            batch.x, batch.edge_index, batch.edge_attr,
            batch.edge_index_seq, batch.edge_attr_seq,
            chain_id,
        )
        resid = getattr(batch, "resid", None)
        loss = pocket_loss(scores, batch.y.float(), chain_id, resid,
                           use_symmetry=use_symmetry)
    else:
        scores = model(batch.x, batch.edge_index, batch.edge_attr)
        loss = focal_loss(scores, batch.y.float())
    return scores, loss


def train_epoch(model, loader: DataLoader, optimizer: torch.optim.Optimizer,
                device: str, use_symmetry: bool = False) -> float:
    """Run one training epoch. Returns mean loss."""
    model.train()
    total_loss = 0.0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        _, loss = _forward(model, batch, use_symmetry)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)


@torch.no_grad()
def eval_epoch(model, loader: DataLoader, device: str) -> dict:
    """Evaluate on loader. Returns dict with loss and AUROC."""
    model.eval()
    total_loss = 0.0
    all_scores: list[np.ndarray] = []
    all_labels: list[np.ndarray] = []

    for batch in loader:
        batch = batch.to(device)
        scores, loss = _forward(model, batch)
        total_loss += loss.item()
        all_scores.append(scores.cpu().numpy())
        all_labels.append(batch.y.cpu().numpy())

    y_score = np.concatenate(all_scores)
    y_true  = np.concatenate(all_labels)

    # AUROC requires at least one positive and one negative sample
    if len(np.unique(y_true)) < 2:
        auroc = float('nan')
    else:
        auroc = roc_auc_score(y_true, y_score)

    return {
        'loss':  total_loss / len(loader),
        'auroc': auroc,
    }


def main(args: argparse.Namespace) -> None:
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    train_set = PocketDataset(args.train_dir)
    val_set   = PocketDataset(args.val_dir)

    use_v2 = args.model_size != 'v1'
    follow = ['edge_index_seq'] if use_v2 else []
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True,
                              follow_batch=follow)
    val_loader   = DataLoader(val_set,   batch_size=args.batch_size,
                              follow_batch=follow)

    if args.model_size == 'small':
        model = PocketGNN.small().to(device)
    elif args.model_size == 'medium':
        model = PocketGNN.medium().to(device)
    elif args.model_size == 'v1':
        model = CrypticGNN().to(device)
    else:
        model = PocketGNN().to(device)  # large

    if args.resume:
        ckpt = Path(args.resume)
        if ckpt.exists():
            model.load_state_dict(torch.load(ckpt, map_location=device))
            print(f"Resumed from {ckpt}")

    use_symmetry = (args.phase == 'finetune')

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    ckpt_dir = Path(args.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    best_auroc = -1.0
    patience_counter = 0

    for epoch in range(1, args.epochs + 1):
        train_loss = train_epoch(model, train_loader, optimizer, device, use_symmetry)
        val_metrics = eval_epoch(model, val_loader, device)
        scheduler.step()

        auroc = val_metrics['auroc']
        print(f"Epoch {epoch:03d} | train_loss={train_loss:.4f} | "
              f"val_loss={val_metrics['loss']:.4f} | AUROC={auroc:.4f}")

        if np.isnan(auroc) or auroc > best_auroc:
            if not np.isnan(auroc):
                best_auroc = auroc
            patience_counter = 0
            torch.save(model.state_dict(), ckpt_dir / 'best.ckpt')
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"Early stopping at epoch {epoch}")
                break

    print(f"Best AUROC: {best_auroc:.4f}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train PocketGNN")
    parser.add_argument('--train_dir',      required=True)
    parser.add_argument('--val_dir',        required=True)
    parser.add_argument('--checkpoint_dir', default='checkpoints/')
    parser.add_argument('--model_size',     default='large',
                        choices=['large', 'medium', 'small', 'v1'])
    parser.add_argument('--phase',          default='pretrain',
                        choices=['pretrain', 'finetune'],
                        help='finetune enables symmetry loss (PCNA only)')
    parser.add_argument('--resume',         default=None,
                        help='path to checkpoint to resume from')
    parser.add_argument('--epochs',         type=int,   default=100)
    parser.add_argument('--batch_size',     type=int,   default=16)
    parser.add_argument('--lr',             type=float, default=1e-3)
    parser.add_argument('--patience',       type=int,   default=10)
    main(parser.parse_args())
