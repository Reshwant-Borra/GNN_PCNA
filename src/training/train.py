"""
Training loop for PocketGNN.
Pre-train on CryptoSite, fine-tune on PCNA (8GLA labels).
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import torch
import numpy as np
from tqdm import tqdm
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from sklearn.metrics import roc_auc_score

from src.models import CrypticGNN, PocketGNN, PocketGNNXL
from src.models.cryptic_gnn import pocket_loss, focal_loss
from .dataset import PocketDataset


def _set_seed(seed: int) -> None:
    """Seed Python, NumPy, and Torch for reproducible training runs."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def _sha256_file(path: Path) -> str:
    """Return the SHA256 digest for one file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _split_hash(path: str | None) -> str | None:
    """Return a stable hash of the split manifest, if provided."""
    if not path:
        return None
    return _sha256_file(Path(path))


def _graph_manifest_hash(split_path: str | None, graph_dir: str | Path) -> str | None:
    """Hash the graph files referenced by a split manifest."""
    if not split_path:
        return None
    manifest = json.loads(Path(split_path).read_text(encoding="utf-8"))
    graph_dir = Path(graph_dir)
    h = hashlib.sha256()
    for split in ("train", "val", "test"):
        for stem in sorted(manifest["splits"].get(split, [])):
            path = graph_dir / f"{stem}.pt"
            h.update(split.encode("utf-8"))
            h.update(stem.encode("utf-8"))
            h.update(_sha256_file(path).encode("ascii"))
    return h.hexdigest()


def _git_commit() -> str | None:
    """Return the current git commit, or None outside a git checkout."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[2],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _environment_summary() -> dict:
    """Collect package and runtime versions needed to interpret a checkpoint."""
    pkgs: dict[str, str | None] = {
        "python": sys.version.split()[0],
        "torch": getattr(torch, "__version__", None),
        "cuda_available": str(torch.cuda.is_available()),
    }
    for mod_name in ("torch_geometric", "torch_scatter", "torch_sparse", "numpy", "sklearn"):
        try:
            mod = __import__(mod_name)
            pkgs[mod_name] = getattr(mod, "__version__", "?")
        except Exception:
            pkgs[mod_name] = None
    return pkgs


def _check_homology_audit(path: str | None, require: bool) -> None:
    """Fail fast when the selected split has no clean homology audit."""
    if not require and not path:
        return
    if not path:
        raise RuntimeError("--require_clean_audit was set but --homology_audit was not provided")
    audit_path = Path(path)
    if not audit_path.exists():
        raise FileNotFoundError(f"Homology audit not found: {audit_path}")
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("leakage_detected", True):
        raise RuntimeError(f"Homology leakage detected in {audit_path}; refusing to train")


# ── sanity check ──────────────────────────────────────────────────────────────

def sanity_check(model: torch.nn.Module, device: str) -> None:
    """
    Forward + backward pass on synthetic data before touching real data.
    Raises AssertionError on any shape or range failure.
    """
    print("  [sanity] running forward/backward on synthetic data...")
    N, E = 24, 50
    E_seq = 2 * (N - 1)          # bidirectional backbone edges

    # Infer node dim from model's first linear layer
    if isinstance(model, PocketGNNXL):
        node_dim = model.node_encoder[0].in_features
    elif isinstance(model, PocketGNN):
        node_dim = model.node_encoder[0].in_features
    else:
        node_dim = 40

    x             = torch.randn(N, node_dim)
    edge_index    = torch.randint(0, N, (2, E))
    edge_attr     = torch.randn(E, 6)
    src_s = torch.arange(N - 1)
    dst_s = torch.arange(1, N)
    edge_index_seq = torch.stack([
        torch.cat([src_s, dst_s]),
        torch.cat([dst_s, src_s]),
    ])
    edge_attr_seq  = torch.randn(E_seq, 6)
    y              = torch.randint(0, 2, (N,)).float()

    data = Data(
        x=x, edge_index=edge_index, edge_attr=edge_attr,
        edge_index_seq=edge_index_seq, edge_attr_seq=edge_attr_seq, y=y,
    ).to(device)

    was_training = model.training
    model.train()

    if isinstance(model, (PocketGNN, PocketGNNXL)):
        scores = model(data.x, data.edge_index, data.edge_attr,
                       data.edge_index_seq, data.edge_attr_seq)
    else:
        scores = model(data.x, data.edge_index, data.edge_attr)

    assert scores.shape == (N,), \
        f"[sanity] FAIL: expected scores ({N},), got {scores.shape}"
    s_min, s_max = scores.detach().min().item(), scores.detach().max().item()
    assert s_min >= 0.0 and s_max <= 1.0, \
        f"[sanity] FAIL: scores out of [0,1]: [{s_min:.4f}, {s_max:.4f}]"

    loss = focal_loss(scores, data.y.to(device))
    loss.backward()

    grad_norms = [p.grad.norm().item() for p in model.parameters() if p.grad is not None]
    assert len(grad_norms) > 0, "[sanity] FAIL: no gradients computed"
    assert all(np.isfinite(g) for g in grad_norms), "[sanity] FAIL: NaN/Inf gradients"

    # Zero grads so they don't interfere with actual training
    model.zero_grad()
    if not was_training:
        model.eval()

    n_params = sum(p.numel() for p in model.parameters())
    print(f"  [sanity] PASS  |  params={n_params:,}  |  "
          f"scores=[{scores.min():.3f},{scores.max():.3f}]  |  loss={loss.item():.4f}")


# ── training ──────────────────────────────────────────────────────────────────

def _maybe_zero_esm(x: torch.Tensor, zero_esm: bool) -> torch.Tensor:
    """Zero ESM2 columns while preserving 40 hand-crafted geometry features."""
    if not zero_esm:
        return x
    if x.shape[1] <= 40:
        return x
    x = x.clone()
    x[:, 40:] = 0.0
    return x


def _forward(model, batch, use_symmetry: bool = False, zero_esm: bool = False):
    x = _maybe_zero_esm(batch.x, zero_esm)
    if isinstance(model, (PocketGNN, PocketGNNXL)):
        chain_id = getattr(batch, "chain_id", None)
        scores = model(
            x, batch.edge_index, batch.edge_attr,
            batch.edge_index_seq, batch.edge_attr_seq,
            chain_id,
        )
        if batch.y is None:
            return scores, scores.sum() * 0.0
        resid = getattr(batch, "resid", None)
        b = getattr(batch, "batch", None)
        loss = pocket_loss(scores, batch.y.float(), chain_id, resid, b,
                           use_symmetry=use_symmetry)
    else:
        scores = model(x, batch.edge_index, batch.edge_attr)
        if batch.y is None:
            return scores, scores.sum() * 0.0
        loss = focal_loss(scores, batch.y.float())
    return scores, loss


def train_epoch(model, loader: DataLoader, optimizer: torch.optim.Optimizer,
                device: str, use_symmetry: bool = False,
                clip_grad: float = 1.0, zero_esm: bool = False) -> float:
    model.train()
    total_loss = 0.0
    bar = tqdm(loader, desc="  train", leave=False, ncols=100, unit="batch")
    for batch in bar:
        batch = batch.to(device)
        optimizer.zero_grad()
        _, loss = _forward(model, batch, use_symmetry, zero_esm)
        loss.backward()
        if clip_grad > 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip_grad)
        optimizer.step()
        total_loss += loss.item()
        bar.set_postfix(loss=f"{loss.item():.4f}")
    return total_loss / max(len(loader), 1)


@torch.no_grad()
def eval_epoch(model, loader: DataLoader, device: str, zero_esm: bool = False) -> dict:
    model.eval()
    total_loss = 0.0
    all_scores: list[np.ndarray] = []
    all_labels: list[np.ndarray] = []

    bar = tqdm(loader, desc="  val  ", leave=False, ncols=100, unit="batch")
    for batch in bar:
        batch = batch.to(device)
        scores, loss = _forward(model, batch, zero_esm=zero_esm)
        total_loss += loss.item()
        if batch.y is None:
            continue
        all_scores.append(scores.cpu().numpy())
        all_labels.append(batch.y.cpu().numpy())

    if not all_scores:
        return {'loss': total_loss / max(len(loader), 1), 'auroc': float('nan')}

    y_score = np.concatenate(all_scores)
    y_true  = np.concatenate(all_labels)

    auroc = float('nan')
    if len(np.unique(y_true)) >= 2:
        auroc = roc_auc_score(y_true, y_score)

    return {
        'loss' : total_loss / max(len(loader), 1),
        'auroc': auroc,
    }


# ── main ──────────────────────────────────────────────────────────────────────

def main(args: argparse.Namespace) -> None:
    _set_seed(args.seed)
    _check_homology_audit(args.homology_audit, args.require_clean_audit)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Device: {device}")

    # ── model ─────────────────────────────────────────────────────────────────
    if args.model_size == 'small':
        model = PocketGNN.small().to(device)
    elif args.model_size == 'medium':
        model = PocketGNN.medium().to(device)
    elif args.model_size == 'v1':
        model = CrypticGNN().to(device)
    elif args.model_size == 'xl':
        model = PocketGNNXL(node_in_dim=args.node_dim).to(device)
    elif args.model_size == 'xl-t6':
        model = PocketGNNXL.from_esm6().to(device)
    else:
        model = PocketGNN().to(device)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"Model: {model.__class__.__name__} ({args.model_size})  |  params={n_params:,}")

    # ── sanity check ──────────────────────────────────────────────────────────
    sanity_check(model, device)

    # ── resume ────────────────────────────────────────────────────────────────
    if args.resume:
        ckpt = Path(args.resume)
        if ckpt.exists():
            model.load_state_dict(torch.load(ckpt, map_location=device, weights_only=True))
            print(f"Resumed from {ckpt}")

    # ── data ──────────────────────────────────────────────────────────────────
    if args.train_manifest:
        graph_dir = args.graph_dir or "data/graphs"
        train_set = PocketDataset.from_manifest(args.train_manifest, "train", graph_dir)
        val_set   = PocketDataset.from_manifest(args.train_manifest, "val",   graph_dir)
    else:
        train_set = PocketDataset(args.train_dir)
        val_set   = PocketDataset(args.val_dir)
    print(f"Train: {len(train_set)} graphs  |  Val: {len(val_set)} graphs")

    use_v2 = args.model_size != 'v1'
    follow = ['edge_index_seq'] if use_v2 else []

    # XL models use the same dual-graph forward signature as PocketGNN v2
    if isinstance(model, PocketGNNXL):
        use_v2 = True
        follow = ['edge_index_seq']
    train_loader = DataLoader(train_set, batch_size=args.batch_size,
                              shuffle=True, follow_batch=follow)
    val_loader   = DataLoader(val_set,   batch_size=args.batch_size,
                              follow_batch=follow)

    use_symmetry = (args.phase == 'finetune')

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    if args.scheduler == 'plateau':
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='max', factor=0.5, patience=args.lr_patience, min_lr=1e-6)
    else:
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    ckpt_dir = Path(args.checkpoint_dir)
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    best_auroc      = -1.0
    patience_counter = 0

    epoch_bar = tqdm(range(1, args.epochs + 1), desc="Epochs", ncols=100, unit="ep")
    for epoch in epoch_bar:
        train_loss  = train_epoch(model, train_loader, optimizer, device,
                                  use_symmetry, args.clip_grad, args.zero_esm)
        val_metrics = eval_epoch(model, val_loader, device, args.zero_esm)
        if args.scheduler == 'plateau':
            scheduler.step(val_metrics['auroc'] if not np.isnan(val_metrics['auroc']) else 0.0)
        else:
            scheduler.step()

        auroc = val_metrics['auroc']
        auroc_str = f"{auroc:.4f}" if not np.isnan(auroc) else "  nan "
        epoch_bar.write(
            f"Epoch {epoch:03d} | train_loss={train_loss:.4f} | "
            f"val_loss={val_metrics['loss']:.4f} | AUROC={auroc_str}"
        )

        is_best = not np.isnan(auroc) and auroc > best_auroc
        if is_best:
            best_auroc = auroc
            patience_counter = 0
            torch.save(model.state_dict(), ckpt_dir / 'best.ckpt')
            meta = {
                "epoch": epoch,
                "val_auroc": round(float(auroc), 6),
                "val_loss": round(float(val_metrics["loss"]), 6),
                "train_loss": round(float(train_loss), 6),
                "model_class": model.__class__.__name__,
                "model_size": args.model_size,
                "n_params": sum(p.numel() for p in model.parameters()),
                "phase": args.phase,
                "resume_ckpt": args.resume or None,
                "train_dir": str(args.train_dir),
                "val_dir": str(args.val_dir),
                "train_manifest": str(args.train_manifest) if args.train_manifest else None,
                "graph_dir": str(args.graph_dir),
                "split_hash": _split_hash(args.train_manifest),
                "graph_manifest_hash": _graph_manifest_hash(args.train_manifest, args.graph_dir),
                "condition": args.condition,
                "node_dim": args.node_dim if args.model_size in {"xl", "xl-t6"} else 40,
                "zero_esm": bool(args.zero_esm),
                "homology_audit": str(args.homology_audit) if args.homology_audit else None,
                "command": " ".join(sys.argv),
                "git_commit": _git_commit(),
                "environment": _environment_summary(),
                "lr": args.lr,
                "weight_decay": args.weight_decay,
                "batch_size": args.batch_size,
                "seed": args.seed,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            (ckpt_dir / "best_meta.json").write_text(
                json.dumps(meta, indent=2), encoding="utf-8"
            )
            epoch_bar.write(f"  -> new best AUROC {best_auroc:.4f}  (saved)")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                epoch_bar.write(f"Early stopping at epoch {epoch} (patience={args.patience})")
                break

    print(f"\nTraining complete. Best val AUROC: {best_auroc:.4f}")
    print(f"Checkpoint: {ckpt_dir / 'best.ckpt'}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train PocketGNN")
    parser.add_argument('--train_dir',       default=None,
                        help='Directory of .pt train graphs (legacy — use --train_manifest instead)')
    parser.add_argument('--val_dir',         default=None,
                        help='Directory of .pt val graphs (legacy)')
    parser.add_argument('--train_manifest',  default=None,
                        help='Path to cryptosite_split.json manifest (preferred over --train_dir)')
    parser.add_argument('--graph_dir',       default='data/graphs',
                        help='Graph directory used with --train_manifest')
    parser.add_argument('--checkpoint_dir', default='checkpoints/')
    parser.add_argument('--model_size',     default='small',
                        choices=['large', 'medium', 'small', 'v1', 'xl', 'xl-t6'],
                        help='xl=PocketGNNXL+ESM2 (520-dim), xl-t6=360-dim, large=10.4M')
    parser.add_argument('--node_dim',       type=int, default=520,
                        help='Node feature dim for xl model (520=ESM2-t12, 360=ESM2-t6)')
    parser.add_argument('--phase',          default='pretrain',
                        choices=['pretrain', 'finetune'],
                        help='finetune enables symmetry loss (PCNA only)')
    parser.add_argument('--resume',         default=None,
                        help='path to checkpoint .ckpt to resume from')
    parser.add_argument('--epochs',         type=int,   default=100)
    parser.add_argument('--batch_size',     type=int,   default=4)
    parser.add_argument('--lr',             type=float, default=3e-4)
    parser.add_argument('--weight_decay',   type=float, default=1e-4)
    parser.add_argument('--patience',       type=int,   default=20)
    parser.add_argument('--clip_grad',      type=float, default=1.0,
                        help='gradient clipping norm (0 = disabled)')
    parser.add_argument('--scheduler',      default='plateau',
                        choices=['cosine', 'plateau'])
    parser.add_argument('--lr_patience',    type=int,   default=7,
                        help='epochs without improvement before LR halved (plateau only)')
    parser.add_argument('--seed',           type=int,   default=42,
                        help='random seed for reproducibility')
    parser.add_argument('--condition',      default=None,
                        help='Benchmark condition label saved into best_meta.json')
    parser.add_argument('--zero_esm',       action='store_true',
                        help='For 520-dim XL graphs, zero columns 40: before model forward')
    parser.add_argument('--homology_audit', default=None,
                        help='Path to homology audit JSON for fail-fast leakage checks')
    parser.add_argument('--require_clean_audit', action='store_true',
                        help='Refuse to train unless --homology_audit exists and reports no leakage')
    args = parser.parse_args()
    if not args.train_manifest and not args.train_dir:
        parser.error("Provide --train_manifest (preferred) or --train_dir")
    main(args)
