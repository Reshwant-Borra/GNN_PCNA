"""
finetune_v3_fixed.py — fixes the three hallucination causes identified in the audit.

CHANGES vs finetune_pcna.py
============================
1. APO NEGATIVE SIGNAL
   Loads 1W60 (apo) and other available apo structures alongside 8GLA.
   AOH residue positions in apo structures are labeled explicitly NEGATIVE (y=0).
   Only those labeled residues contribute to the apo loss — the model must learn
   to suppress scores at the AOH site when the pocket is not open.

2. ESM2 SHUFFLE AUGMENTATION
   During each training step, with probability p_esm_shuffle=0.3, the ESM2
   embedding rows are randomly permuted. This prevents the model from relying on
   positional ESM2 alignment (the root cause of H5: row shuffle drops AUROC 0.43).
   The structural branch must carry the discriminative load.

3. POCKET_LOSS (focal + ranking + symmetry)
   Replaces the plain focal_loss call with pocket_loss(), which includes:
     - focal_loss (unchanged)
     - w_rank * ranking_loss: forces pocket residues to score above non-pocket
     - w_sym  * symmetry_loss: penalises variance across homotrimer chains

Usage
-----
    python scripts/finetune_v3_fixed.py
    python scripts/finetune_v3_fixed.py --epochs 80 --p_shuffle 0.3 --w_apo 1.0
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
import numpy as np
from sklearn.metrics import roc_auc_score

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.models.cryptic_gnn import PocketGNNXL, focal_loss, ranking_loss, pocket_loss
from src.data_processing.parse_pdb import parse_pdb
from src.data_processing.graph_construction import build_graph_v2

ESM_DIR  = REPO_ROOT / "data" / "esm_features"
CKPT_V3  = REPO_ROOT / "checkpoints" / "pcna" / "best_pcna_v3.ckpt"
OUT_CKPT = REPO_ROOT / "checkpoints" / "pcna" / "best_pcna_v3_fixed.ckpt"

# AOH1996 ground-truth residue IDs — same for all PCNA chains (same sequence)
AOH_GT = {25,26,27,38,39,40,41,42,44,45,46,47,
           123,125,126,128,231,232,233,234,250,251,252,253}

# Apo structures to use as negative signal.
# Any PCNA structure without AOH1996 bound can serve here.
# Format: (pdb_id, chains_to_use)
APO_STRUCTURES = [
    ("1W60", ["A", "B"]),   # canonical apo, 2 chains, same sequence
]

# Additional holo structures to use as extra positive signal (held-out from val)
# Comment out any you want to keep as test-only
EXTRA_HOLO = [
    # ("8GL9", ["A", "B"]),  # another holo — would give more positive signal
]


# ── helpers ───────────────────────────────────────────────────────────────────

def load_graph_and_esm(pdb_id: str) -> tuple | None:
    """Returns (graph_data, esm_np) or None if files missing."""
    raw = REPO_ROOT / "data" / "raw" / f"{pdb_id}.pdb"
    esm = ESM_DIR / f"{pdb_id}.npy"
    if not raw.exists():
        print(f"  [SKIP] {pdb_id}: no PDB at {raw}")
        return None
    if not esm.exists():
        print(f"  [SKIP] {pdb_id}: no ESM2 at {esm} — run build_esm_features.py first")
        return None
    residues = parse_pdb(raw)
    data     = build_graph_v2(residues)
    esm_np   = np.load(str(esm)).astype(np.float32)
    if data.x.shape[0] != esm_np.shape[0]:
        print(f"  [SKIP] {pdb_id}: graph {data.x.shape[0]} != ESM {esm_np.shape[0]}")
        return None
    return data, esm_np, residues


def make_apo_labels(data, residues: list, chains: list[str]) -> torch.Tensor | None:
    """
    For an apo structure: label AOH residue positions as 0 (explicitly negative),
    all other positions as -1 (ignore in loss).
    Returns float tensor of shape (N,) with values in {-1.0, 0.0}.
    """
    n = data.x.shape[0]
    labels = torch.full((n,), -1.0)   # -1 = ignore

    for i, r in enumerate(residues):
        if r.chain in chains and r.resid in AOH_GT:
            labels[i] = 0.0            # explicitly negative: pocket is NOT open here

    n_neg = int((labels == 0).sum())
    if n_neg == 0:
        print(f"  WARNING: no AOH residues found in chains {chains} — check chain IDs")
        return None
    return labels


def make_holo_labels(data, residues: list, train_chain: str,
                     val_chain: str) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    For 8GLA: label pocket residues in train_chain as 1, non-pocket as 0.
    val_chain labels for AUROC monitoring. All others ignored (-1).
    Returns (labels_full, train_mask, val_mask).
    """
    n = data.x.shape[0]
    labels = torch.full((n,), -1.0)

    train_mask = torch.zeros(n, dtype=torch.bool)
    val_mask   = torch.zeros(n, dtype=torch.bool)

    for i, r in enumerate(residues):
        if r.chain == train_chain:
            train_mask[i] = True
            labels[i] = 1.0 if r.resid in AOH_GT else 0.0
        elif r.chain == val_chain:
            val_mask[i] = True
            labels[i] = 1.0 if r.resid in AOH_GT else 0.0

    return labels, train_mask, val_mask


def forward_xl(model, data, esm_np: np.ndarray,
               p_shuffle: float = 0.0) -> torch.Tensor:
    """
    Forward pass for PocketGNNXL.
    If p_shuffle > 0 and model is in training mode, randomly permutes ESM2 rows
    with probability p_shuffle — forces structural branch to carry the load.
    """
    esm = torch.from_numpy(esm_np)

    # FIX 2: ESM2 shuffle augmentation
    if model.training and p_shuffle > 0 and torch.rand(1).item() < p_shuffle:
        idx = torch.randperm(esm.shape[0])
        esm = esm[idx]

    x_in = torch.cat([data.x, esm], dim=1)
    return model(x_in, data.edge_index, data.edge_attr,
                 data.edge_index_seq, data.edge_attr_seq, data.chain_id)


def compute_loss_holo(scores, labels, train_mask,
                      w_rank: float, margin: float,
                      w_sym: float, data) -> torch.Tensor:
    """FIX 3: pocket_loss (focal + ranking + symmetry) on holo train chain."""
    sc = scores[train_mask]
    y  = labels[train_mask]
    # pocket_loss = focal + w_rank * ranking + w_sym * symmetry
    return pocket_loss(
        sc, y,
        chain_id     = data.chain_id[train_mask] if w_sym > 0 else None,
        resid        = data.resid[train_mask]    if w_sym > 0 else None,
        use_symmetry = w_sym > 0,
        w_rank       = w_rank,
        w_sym        = w_sym,
    )


def compute_loss_apo(scores, labels, w_apo: float) -> torch.Tensor:
    """
    FIX 1: apo negative signal.
    Only compute loss on residues labeled 0 (the AOH positions that should be low).
    Uses focal loss with inverted alpha — the model should strongly predict 0 here.
    """
    mask = labels >= 0          # only the explicitly labeled (negative) residues
    if not mask.any():
        return scores.new_zeros(1).squeeze()
    sc = scores[mask]
    y  = labels[mask]           # all zeros (negative class)
    return w_apo * focal_loss(sc, y, gamma=2.0)


# ── main ──────────────────────────────────────────────────────────────────────

def main(args: argparse.Namespace) -> None:
    device = "cpu"

    # ── Load 8GLA (holo, train=chainA, val=chainB) ────────────────────────────
    print("Loading 8GLA (holo)...")
    result = load_graph_and_esm("8GLA")
    if result is None:
        raise RuntimeError("8GLA is required — cannot continue")
    data_holo, esm_holo, res_holo = result
    labels_holo, train_mask, val_mask = make_holo_labels(
        data_holo, res_holo, train_chain="A", val_chain="B")
    n_train_pos = int((labels_holo[train_mask] == 1).sum())
    n_val_pos   = int((labels_holo[val_mask]   == 1).sum())
    print(f"  8GLA trainA: {train_mask.sum()} residues ({n_train_pos} pocket)  "
          f"valB: {val_mask.sum()} residues ({n_val_pos} pocket)")

    # ── Load apo structures (FIX 1) ───────────────────────────────────────────
    apo_items = []
    print("\nLoading apo structures (negative signal)...")
    for pdb_id, chains in APO_STRUCTURES:
        result = load_graph_and_esm(pdb_id)
        if result is None:
            continue
        data_apo, esm_apo, res_apo = result
        labels_apo = make_apo_labels(data_apo, res_apo, chains)
        if labels_apo is None:
            continue
        n_neg = int((labels_apo == 0).sum())
        print(f"  {pdb_id} chains {chains}: {n_neg} AOH residues labeled negative")
        apo_items.append((pdb_id, data_apo, esm_apo, labels_apo))

    if not apo_items:
        print("  WARNING: no apo structures loaded — FIX 1 will have no effect")

    # ── Model ─────────────────────────────────────────────────────────────────
    print(f"\nLoading PocketGNNXL from {CKPT_V3}...")
    model = PocketGNNXL().to(device)
    sd = torch.load(str(CKPT_V3), map_location=device, weights_only=True)
    model.load_state_dict(sd)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  {n_params:,} parameters loaded")

    # ── Optimizer ─────────────────────────────────────────────────────────────
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.wd)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    OUT_CKPT.parent.mkdir(parents=True, exist_ok=True)
    best_auroc_B = 0.0
    patience_counter = 0

    print(f"\nTraining: {args.epochs} epochs | "
          f"p_shuffle={args.p_shuffle} | w_apo={args.w_apo} | "
          f"w_rank={args.w_rank} | w_sym={args.w_sym}")
    print(f"{'Ep':>4} | {'Loss_H':>8} | {'Loss_A':>8} | "
          f"{'AUROC_A':>8} | {'AUROC_B':>8} | {'FP_apo%':>8} | Best?")
    print("-" * 72)

    for epoch in range(1, args.epochs + 1):
        model.train()
        optimizer.zero_grad()

        # ── Holo forward + loss ───────────────────────────────────────────────
        sc_holo = forward_xl(model, data_holo, esm_holo, args.p_shuffle)
        loss_h  = compute_loss_holo(
            sc_holo, labels_holo, train_mask,
            args.w_rank, args.margin, args.w_sym, data_holo)

        # ── Apo forward + loss (FIX 1) ────────────────────────────────────────
        loss_a = sc_holo.new_zeros(1).squeeze()
        for _, data_apo, esm_apo, labels_apo in apo_items:
            sc_apo = forward_xl(model, data_apo, esm_apo, args.p_shuffle)
            loss_a = loss_a + compute_loss_apo(sc_apo, labels_apo, args.w_apo)
        if apo_items:
            loss_a = loss_a / len(apo_items)

        total_loss = loss_h + loss_a
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()

        # ── Evaluate ──────────────────────────────────────────────────────────
        model.eval()
        with torch.no_grad():
            sc_h_np = forward_xl(model, data_holo, esm_holo).numpy()

        y_h = labels_holo.numpy()
        auroc_A = roc_auc_score(y_h[train_mask], sc_h_np[train_mask]) \
                  if n_train_pos >= 2 else float("nan")
        auroc_B = roc_auc_score(y_h[val_mask],   sc_h_np[val_mask]) \
                  if n_val_pos   >= 2 else float("nan")

        # FP rate on apo AOH positions — KEY NEW METRIC
        fp_apo = float("nan")
        if apo_items:
            apo_fp_rates = []
            for _, data_apo, esm_apo, labels_apo in apo_items:
                with torch.no_grad():
                    sc_apo_np = forward_xl(model, data_apo, esm_apo).numpy()
                apo_neg_mask = labels_apo.numpy() == 0
                apo_fp_rates.append(float((sc_apo_np[apo_neg_mask] > args.threshold).mean()))
            fp_apo = np.mean(apo_fp_rates) * 100

        is_best = not np.isnan(auroc_B) and auroc_B > best_auroc_B
        if is_best:
            best_auroc_B = auroc_B
            patience_counter = 0
            torch.save(model.state_dict(), OUT_CKPT)
        else:
            patience_counter += 1

        marker = " <--" if is_best else ""
        fp_str = f"{fp_apo:7.1f}%" if not np.isnan(fp_apo) else "     N/A"
        print(f"{epoch:4d} | {loss_h.item():8.4f} | {loss_a.item():8.4f} | "
              f"{auroc_A:8.4f} | {auroc_B:8.4f} | {fp_str} |{marker}")

        if patience_counter >= args.patience:
            print(f"\nEarly stopping at epoch {epoch} (patience={args.patience})")
            break

    print(f"\nBest val AUROC (chain B): {best_auroc_B:.4f}")
    print(f"Checkpoint: {OUT_CKPT}")

    # ── Final eval: holo AUROC + apo FP rate ─────────────────────────────────
    model.load_state_dict(torch.load(str(OUT_CKPT), map_location=device, weights_only=True))
    model.eval()

    print("\n=== Final evaluation ===")
    with torch.no_grad():
        sc_final = forward_xl(model, data_holo, esm_holo).numpy()
    y_np = labels_holo.numpy()
    for label, mask in [("trainA", train_mask), ("valB", val_mask)]:
        sc = sc_final[mask.numpy()]
        y  = y_np[mask.numpy()]
        if y.sum() >= 2:
            print(f"  8GLA {label}: AUROC={roc_auc_score(y, sc):.4f}  "
                  f"above {args.threshold:.2f}: {(sc > args.threshold).sum()}/{len(sc)}")

    # Apo FP rate — ideally near 0%
    print("\n  Apo AOH-position FP rate (should approach 0% with fix):")
    for pdb_id, data_apo, esm_apo, labels_apo in apo_items:
        with torch.no_grad():
            sc_apo = forward_xl(model, data_apo, esm_apo).numpy()
        apo_mask = labels_apo.numpy() == 0
        fp = float((sc_apo[apo_mask] > args.threshold).mean()) * 100
        mean_sc = sc_apo[apo_mask].mean()
        print(f"  {pdb_id}: mean_score={mean_sc:.4f}  FP>{args.threshold:.2f}: {fp:.1f}%")

    # ESM2 ablation — quick sanity check on whether structural branch improved
    print("\n  ESM2 ablation AUROC (structural features only — should be higher than before):")
    with torch.no_grad():
        esm_zero = np.zeros_like(esm_holo)
        x_zero   = torch.cat([data_holo.x, torch.from_numpy(esm_zero)], dim=1)
        sc_zero  = model(x_zero, data_holo.edge_index, data_holo.edge_attr,
                         data_holo.edge_index_seq, data_holo.edge_attr_seq,
                         data_holo.chain_id).numpy()
    a_zero = roc_auc_score(y_np[train_mask.numpy()], sc_zero[train_mask.numpy()])
    a_full_final = roc_auc_score(y_np[train_mask.numpy()], sc_final[train_mask.numpy()])
    print(f"  Full ESM2: {a_full_final:.4f}  |  Zero ESM2: {a_zero:.4f}  "
          f"|  ESM2 contribution: {a_full_final - a_zero:+.4f}")
    print(f"  (Before fix: full=0.9971  zero=0.7974  contribution=+0.1997)")
    print(f"  Goal: ESM2 contribution < 0.10 and zero-ESM2 AUROC > 0.85")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="V3 hallucination fix — fine-tune PocketGNNXL")
    parser.add_argument("--epochs",    type=int,   default=60)
    parser.add_argument("--lr",        type=float, default=2e-4,
                        help="Lower LR than original (2e-4 vs 5e-4) — we are fine-tuning a fine-tune")
    parser.add_argument("--wd",        type=float, default=1e-4)
    parser.add_argument("--p_shuffle", type=float, default=0.3,
                        help="Probability of shuffling ESM2 rows per batch (FIX 2)")
    parser.add_argument("--w_apo",     type=float, default=1.0,
                        help="Weight on apo negative loss relative to holo loss (FIX 1)")
    parser.add_argument("--w_rank",    type=float, default=0.3,
                        help="Ranking loss weight (FIX 3)")
    parser.add_argument("--w_sym",     type=float, default=0.05,
                        help="Symmetry loss weight (FIX 3)")
    parser.add_argument("--margin",    type=float, default=0.3)
    parser.add_argument("--patience",  type=int,   default=15)
    parser.add_argument("--threshold", type=float, default=0.4)
    main(parser.parse_args())
