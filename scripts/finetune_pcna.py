"""
PCNA fine-tuning on 8GLA with cross-structure validation on 1W60 (apo).

Strategy
--------
Training: chain A of 8GLA (holo — pocket open, AOH1996 bound).
Validation criterion: pocket discrimination score on two DIFFERENT structures:
  - score_holo  = mean score over AOH1996-labeled residues in 8GLA (all chains)
  - score_apo   = mean score over ALL residues in 1W60 (apo — pocket closed)
  - disc_score  = score_holo - score_apo  (maximise)

This is genuine cross-structure validation: 1W60 is a different crystal structure
from 8GLA. The model is rewarded for scoring the open pocket high AND the closed
apo structure low — learning the structural difference between conformations.

Chain B AUROC is also logged as a symmetry check (same crystal, not independent).

Usage
-----
    python scripts/finetune_pcna.py
    python scripts/finetune_pcna.py --pretrain checkpoints/best.ckpt --epochs 60

Usage
-----
    python scripts/finetune_pcna.py
    python scripts/finetune_pcna.py --pretrain checkpoints/best.ckpt --epochs 60
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import torch
import numpy as np
from sklearn.metrics import roc_auc_score

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.models import PocketGNN
from src.models.cryptic_gnn import focal_loss, ranking_loss
from src.data_processing.parse_pdb import parse_pdb
from src.data_processing.graph_construction import build_graph_v2


def load_8gla() -> tuple:
    """Returns (data, chain_masks) where chain_masks is dict chain_letter -> bool tensor."""
    pt = REPO_ROOT / "data" / "pcna" / "8GLA.pt"
    data = torch.load(pt, weights_only=False)

    # chain_id: 0=A, 1=B, 2=C, 3=D
    masks = {
        "A": data.chain_id == 0,
        "B": data.chain_id == 1,
        "C": data.chain_id == 2,
    }
    return data, masks


def infer(model, data):
    model.eval()
    with torch.no_grad():
        return model(
            data.x, data.edge_index, data.edge_attr,
            data.edge_index_seq, data.edge_attr_seq,
            data.chain_id,
        )


def main(args: argparse.Namespace) -> None:
    device = "cpu"

    # ── load 8GLA (holo) ──────────────────────────────────────────────────────
    data, masks = load_8gla()
    y = data.y.float()

    mask_A, mask_B, mask_C = masks["A"], masks["B"], masks["C"]
    pocket_mask = y.bool()   # all labeled residues across all chains

    n_A_pos = int(y[mask_A].sum())
    n_B_pos = int(y[mask_B].sum())
    print(f"8GLA chains: A={mask_A.sum()} res ({n_A_pos} pocket)  "
          f"B={mask_B.sum()} res ({n_B_pos} pocket)  "
          f"C={mask_C.sum()} res (unlabeled)")

    # ── load 1W60 (apo — cross-structure validation) ──────────────────────────
    apo_path = REPO_ROOT / "data" / "raw" / "1W60.pdb"
    d_apo = None
    if apo_path.exists():
        residues_apo = parse_pdb(apo_path)
        d_apo = build_graph_v2(residues_apo)
        print(f"1W60 apo loaded: {d_apo.x.shape[0]} residues (cross-structure validator)")
    else:
        print("Warning: 1W60.pdb not found — disc_score will use chain B AUROC only")

    print(f"Validation: disc_score = mean(8GLA pocket scores) - mean(1W60 all scores)")

    if n_A_pos == 0:
        raise RuntimeError("No pocket residues in chain A — check 8GLA labels.")

    # ── model ─────────────────────────────────────────────────────────────────
    if args.model_size == "small":
        model = PocketGNN.small().to(device)
    elif args.model_size == "medium":
        model = PocketGNN.medium().to(device)
    else:
        model = PocketGNN().to(device)

    if args.pretrain and Path(args.pretrain).exists():
        model.load_state_dict(
            torch.load(args.pretrain, map_location=device, weights_only=True))
        print(f"Loaded pre-trained weights: {args.pretrain}")
    else:
        print("Warning: no pre-trained weights — fine-tuning from scratch")

    # ── optimizer ─────────────────────────────────────────────────────────────
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=args.wd)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs)

    ckpt_dir = REPO_ROOT / "checkpoints" / "pcna"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    best_disc = -1.0
    patience_counter = 0

    print(f"\n{'Ep':>4} | {'LossA':>7} | {'AUROC_B':>8} | {'disc':>7} | "
          f"{'holo':>6} | {'apo':>6} | {'Best?'}")
    print("-" * 68)

    for epoch in range(1, args.epochs + 1):
        # ── train on chain A ──────────────────────────────────────────────────
        model.train()
        optimizer.zero_grad()

        scores_all = model(
            data.x, data.edge_index, data.edge_attr,
            data.edge_index_seq, data.edge_attr_seq,
            data.chain_id,
        )

        sc_A = scores_all[mask_A]
        y_A  = y[mask_A]
        loss = (focal_loss(sc_A, y_A, gamma=2.0)
                + args.w_rank * ranking_loss(sc_A, y_A, margin=args.margin))
        loss.backward()
        optimizer.step()
        scheduler.step()

        # ── evaluate ──────────────────────────────────────────────────────────
        model.eval()
        with torch.no_grad():
            sc_all = model(
                data.x, data.edge_index, data.edge_attr,
                data.edge_index_seq, data.edge_attr_seq,
                data.chain_id,
            ).numpy()

        sc_B_np = sc_all[mask_B.numpy()]
        y_B_np  = y[mask_B].numpy()
        auroc_B = roc_auc_score(y_B_np, sc_B_np) if y_B_np.sum() >= 2 else float("nan")

        # Cross-structure validation: discrimination score
        mean_holo = float(sc_all[pocket_mask.numpy()].mean())
        if d_apo is not None:
            with torch.no_grad():
                sc_apo_np = model(
                    d_apo.x, d_apo.edge_index, d_apo.edge_attr,
                    d_apo.edge_index_seq, d_apo.edge_attr_seq,
                    d_apo.chain_id,
                ).numpy()
            mean_apo  = float(sc_apo_np.mean())
            disc_score = mean_holo - mean_apo
        else:
            mean_apo   = float("nan")
            disc_score = auroc_B if not np.isnan(auroc_B) else -1.0

        is_best = disc_score > best_disc
        if is_best:
            best_disc = disc_score
            patience_counter = 0
            torch.save(model.state_dict(), ckpt_dir / "best_pcna.ckpt")
            meta = {
                "epoch": epoch,
                "val_criterion": "disc_score = mean(8GLA pocket) - mean(1W60 apo)",
                "disc_score": round(disc_score, 6),
                "mean_holo_pocket_score": round(mean_holo, 6),
                "mean_apo_score": round(mean_apo, 6) if not np.isnan(mean_apo) else None,
                "auroc_chain_b_symmetry_check": round(float(auroc_B), 6) if not np.isnan(auroc_B) else None,
                "train_loss": round(float(loss.item()), 6),
                "model_size": args.model_size,
                "pretrain_ckpt": args.pretrain,
                "lr": args.lr,
                "wd": args.wd,
                "seed": args.seed,
                "validation_note": (
                    "Cross-structure validation: disc_score uses 8GLA (holo) and 1W60 (apo), "
                    "two different crystal structures. Chain B AUROC is a symmetry check only."
                ),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            (ckpt_dir / "best_pcna_meta.json").write_text(
                json.dumps(meta, indent=2), encoding="utf-8"
            )
        else:
            patience_counter += 1

        marker = " <--" if is_best else ""
        apo_str = f"{mean_apo:.4f}" if not np.isnan(mean_apo) else "  n/a"
        print(f"{epoch:4d} | {loss.item():7.4f} | {auroc_B:8.4f} | "
              f"{disc_score:7.4f} | {mean_holo:.4f} | {apo_str} |{marker}")

        if patience_counter >= args.patience:
            print(f"\nEarly stopping (patience={args.patience})")
            break

    print(f"\nBest disc_score: {best_disc:.4f}")
    print(f"Saved: {ckpt_dir / 'best_pcna.ckpt'}")

    # ── final evaluation ──────────────────────────────────────────────────────
    model.load_state_dict(
        torch.load(ckpt_dir / "best_pcna.ckpt", map_location=device, weights_only=True))
    model.eval()

    with torch.no_grad():
        sc_final = model(
            data.x, data.edge_index, data.edge_attr,
            data.edge_index_seq, data.edge_attr_seq,
            data.chain_id,
        ).numpy()

    y_np = y.numpy()
    print("\n=== Final 8GLA evaluation ===")
    for ch, msk in [("A", mask_A), ("B", mask_B), ("C", mask_C)]:
        sc = sc_final[msk.numpy()]
        gt = y_np[msk.numpy()]
        if gt.sum() >= 2:
            auroc = roc_auc_score(gt, sc)
            top50_rec = gt[np.argsort(sc)[-50:]].sum() / gt.sum()
            print(f"  Chain {ch}: AUROC={auroc:.4f}  recall@50={top50_rec:.3f}  "
                  f"above {args.threshold:.2f}: {(sc>args.threshold).sum()}/{len(sc)}")
        else:
            fp = (sc > args.threshold).sum()
            print(f"  Chain {ch}: (no labels)  FP above {args.threshold:.2f}: {fp}/{len(sc)}")

    # ── test on 1W60 (apo) ────────────────────────────────────────────────────
    apo_path = REPO_ROOT / "data" / "raw" / "1W60.pdb"
    if apo_path.exists():
        residues = parse_pdb(apo_path)
        d_apo    = build_graph_v2(residues)
        with torch.no_grad():
            sc_apo = model(
                d_apo.x, d_apo.edge_index, d_apo.edge_attr,
                d_apo.edge_index_seq, d_apo.edge_attr_seq,
                d_apo.chain_id,
            ).numpy()
        top20 = np.argsort(sc_apo)[-20:][::-1]
        n_above = int((sc_apo > args.threshold).sum())
        print(f"\n=== 1W60 (apo) ===")
        print(f"  Score range [{sc_apo.min():.3f}, {sc_apo.max():.3f}]  "
              f"above {args.threshold:.2f}: {n_above}/{len(sc_apo)}")
        print("  Top-10 predicted pocket residues:")
        for i in top20[:10]:
            r = residues[i]
            print(f"    {r.chain}{r.resid:4d} {r.resname:3s}  score={sc_apo[i]:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PCNA fine-tuning on 8GLA")
    parser.add_argument("--pretrain",   default="checkpoints/best.ckpt",
                        help="Pre-trained checkpoint to start from")
    parser.add_argument("--model_size", default="small",
                        choices=["small", "medium", "large"])
    parser.add_argument("--epochs",     type=int,   default=80)
    parser.add_argument("--lr",         type=float, default=5e-4)
    parser.add_argument("--wd",         type=float, default=1e-4)
    parser.add_argument("--w_rank",     type=float, default=0.3,
                        help="Weight for ranking loss (default 0.3)")
    parser.add_argument("--margin",     type=float, default=0.3,
                        help="Ranking loss margin (default 0.3)")
    parser.add_argument("--patience",   type=int,   default=20)
    parser.add_argument("--threshold",  type=float, default=0.4)
    parser.add_argument("--seed",       type=int,   default=42)
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    main(args)
