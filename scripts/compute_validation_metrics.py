"""
Compute extended validation metrics for PocketGNNXL on held-out CryptoSite structures.

Outputs:
  data/results/extended_metrics.json       -- all metrics
  data/results/fig5_validation_panel.png   -- 4-panel publication figure
"""
from __future__ import annotations
import json, sys, os
import numpy as np
import torch

# ── paths ──────────────────────────────────────────────────────────────────────
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ".")

from pathlib import Path
REPO = Path(".")
CKPT = REPO / "checkpoints/pcna_reproduced/best.ckpt"
SPLIT = REPO / "data/splits/cryptosite_split.json"
GRAPHS = REPO / "data/graphs_xl"
OUT_JSON = REPO / "data/results/extended_metrics.json"
OUT_FIG  = REPO / "data/results/fig5_validation_panel.png"

# ── imports ────────────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from sklearn.metrics import (
    roc_auc_score, average_precision_score,
    matthews_corrcoef, precision_recall_curve, roc_curve,
)

from src.models import PocketGNNXL

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {DEVICE}")

# ── load model ─────────────────────────────────────────────────────────────────
print("Loading checkpoint...")
ckpt = torch.load(str(CKPT), map_location=DEVICE, weights_only=False)
state = ckpt.get("model_state_dict", ckpt.get("state_dict", ckpt))

model = PocketGNNXL(node_in_dim=520)
model.load_state_dict(state, strict=False)
model.to(DEVICE)
model.eval()
print(f"  Model loaded: {sum(p.numel() for p in model.parameters()):,} params")

# ── inference ──────────────────────────────────────────────────────────────────
split = json.loads(SPLIT.read_text())["splits"]
VAL_IDS  = split["val"]
TEST_IDS = split["test"]
ALL_IDS  = VAL_IDS + TEST_IDS

all_scores, all_labels = [], []
per_struct = {}

print("Running inference on held-out structures...")
with torch.no_grad():
    for pdb_id in ALL_IDS:
        pt_path = GRAPHS / f"{pdb_id}.pt"
        if not pt_path.exists():
            print(f"  SKIP {pdb_id}: graph not found")
            continue
        data = torch.load(str(pt_path), weights_only=False)
        if not hasattr(data, "y") or data.y is None:
            print(f"  SKIP {pdb_id}: no labels")
            continue

        x          = data.x.to(DEVICE)
        edge_index = data.edge_index.to(DEVICE)
        edge_attr  = data.edge_attr.to(DEVICE)
        edge_index_seq = data.edge_index_seq.to(DEVICE)
        edge_attr_seq  = data.edge_attr_seq.to(DEVICE)
        y = data.y.numpy()

        scores = model(x, edge_index, edge_attr, edge_index_seq, edge_attr_seq)
        scores = scores.cpu().numpy()

        n_pos = int(y.sum())
        if n_pos < 2 or n_pos == len(y):
            print(f"  SKIP {pdb_id}: degenerate labels (pos={n_pos}/{len(y)})")
            continue

        auroc  = float(roc_auc_score(y, scores))
        auprc  = float(average_precision_score(y, scores))

        # Optimal MCC threshold (grid search)
        best_mcc, best_thr = -1.0, 0.5
        for thr in np.linspace(0.1, 0.9, 81):
            preds = (scores >= thr).astype(int)
            mcc = matthews_corrcoef(y, preds)
            if mcc > best_mcc:
                best_mcc, best_thr = mcc, float(thr)

        # Enrichment factor EF1% and EF5%
        n_total  = len(y)
        pos_rate = y.mean()
        def enrichment_factor(pct):
            k = max(1, int(np.ceil(n_total * pct / 100)))
            top_idx = np.argsort(scores)[::-1][:k]
            hits = y[top_idx].sum()
            return float((hits / k) / pos_rate) if pos_rate > 0 else 0.0

        ef1  = enrichment_factor(1)
        ef5  = enrichment_factor(5)
        ef10 = enrichment_factor(10)

        # Top-K precision/recall (K = n_pos)
        top_k_idx = np.argsort(scores)[::-1][:n_pos]
        prec_k = float(y[top_k_idx].mean())
        rec_k  = float(y[top_k_idx].sum() / n_pos)

        per_struct[pdb_id] = {
            "split": "val" if pdb_id in VAL_IDS else "test",
            "n_residues": n_total,
            "n_positive":  n_pos,
            "auroc":  round(auroc, 4),
            "auprc":  round(auprc, 4),
            "mcc":    round(best_mcc, 4),
            "mcc_threshold": round(best_thr, 3),
            "ef1":    round(ef1, 3),
            "ef5":    round(ef5, 3),
            "ef10":   round(ef10, 3),
            "precision_at_k": round(prec_k, 4),
            "recall_at_k":    round(rec_k, 4),
        }

        all_scores.extend(scores.tolist())
        all_labels.extend(y.tolist())
        set_label = "val" if pdb_id in VAL_IDS else "TEST"
        print(f"  [{set_label}] {pdb_id:6s}  AUROC={auroc:.4f}  MCC={best_mcc:.4f}  EF1={ef1:.2f}x  EF5={ef5:.2f}x")

# ── pooled metrics ─────────────────────────────────────────────────────────────
all_scores = np.array(all_scores)
all_labels = np.array(all_labels)

pooled_auroc = float(roc_auc_score(all_labels, all_scores))
pooled_auprc = float(average_precision_score(all_labels, all_scores))
trivial_auprc = float(all_labels.mean())

# pooled optimal MCC
best_mcc_pooled, best_thr_pooled = -1.0, 0.5
for thr in np.linspace(0.05, 0.95, 91):
    preds = (all_scores >= thr).astype(int)
    mcc = matthews_corrcoef(all_labels, preds)
    if mcc > best_mcc_pooled:
        best_mcc_pooled, best_thr_pooled = mcc, float(thr)

# pooled EFs
def ef_pooled(pct):
    k = max(1, int(np.ceil(len(all_labels) * pct / 100)))
    top_idx = np.argsort(all_scores)[::-1][:k]
    pos_rate = all_labels.mean()
    hits = all_labels[top_idx].sum()
    return float((hits / k) / pos_rate) if pos_rate > 0 else 0.0

pooled_ef1  = ef_pooled(1)
pooled_ef5  = ef_pooled(5)
pooled_ef10 = ef_pooled(10)

# Bootstrap 95% CI for AUROC (n=2000)
print("\nBootstrap CI for AUROC (n=2000)...")
rng = np.random.default_rng(42)
boot_aurocs = []
for _ in range(2000):
    idx = rng.choice(len(all_labels), size=len(all_labels), replace=True)
    if all_labels[idx].sum() == 0 or all_labels[idx].sum() == len(idx):
        continue
    boot_aurocs.append(roc_auc_score(all_labels[idx], all_scores[idx]))
ci_lo, ci_hi = np.percentile(boot_aurocs, [2.5, 97.5])

# mean per-structure metrics
val_structs  = [v for k, v in per_struct.items() if v["split"] == "val"]
test_structs = [v for k, v in per_struct.items() if v["split"] == "test"]

def mean_metric(structs, key):
    vals = [s[key] for s in structs if key in s]
    return round(float(np.mean(vals)), 4) if vals else None

summary = {
    "pooled": {
        "n_structures": len(per_struct),
        "n_residues":   int(len(all_labels)),
        "n_positive":   int(all_labels.sum()),
        "auroc":        round(pooled_auroc, 4),
        "auroc_ci_95":  [round(ci_lo, 4), round(ci_hi, 4)],
        "auprc":        round(pooled_auprc, 4),
        "trivial_auprc": round(trivial_auprc, 4),
        "lift_above_trivial": round(pooled_auprc / trivial_auprc, 2),
        "mcc":          round(best_mcc_pooled, 4),
        "mcc_threshold": round(best_thr_pooled, 3),
        "ef1":          round(pooled_ef1, 3),
        "ef5":          round(pooled_ef5, 3),
        "ef10":         round(pooled_ef10, 3),
    },
    "val_mean":  {k: mean_metric(val_structs, k)  for k in ["auroc","auprc","mcc","ef1","ef5","precision_at_k","recall_at_k"]},
    "test_mean": {k: mean_metric(test_structs, k) for k in ["auroc","auprc","mcc","ef1","ef5","precision_at_k","recall_at_k"]},
    "per_structure": per_struct,
}

OUT_JSON.write_text(json.dumps(summary, indent=2))
print(f"\nMetrics saved: {OUT_JSON}")
print(f"\n=== POOLED RESULTS ===")
print(f"  AUROC  = {pooled_auroc:.4f}  95% CI [{ci_lo:.4f}, {ci_hi:.4f}]")
print(f"  AUPRC  = {pooled_auprc:.4f}  (trivial baseline = {trivial_auprc:.4f}, lift = {pooled_auprc/trivial_auprc:.1f}x)")
print(f"  MCC    = {best_mcc_pooled:.4f}  (threshold = {best_thr_pooled:.2f})")
print(f"  EF1%   = {pooled_ef1:.2f}x")
print(f"  EF5%   = {pooled_ef5:.2f}x")
print(f"  EF10%  = {pooled_ef10:.2f}x")

# ── FIGURE ─────────────────────────────────────────────────────────────────────
print("\nGenerating validation panel figure...")

BLUE   = "#4878CF"
RED    = "#E84646"
ORANGE = "#F5A623"
GRAY   = "#AAAAAA"
GREEN  = "#2ECC71"
DARK   = "#2C3E50"

fig = plt.figure(figsize=(12, 10))
fig.patch.set_facecolor("#F8F9FA")
gs  = gridspec.GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.38,
                        left=0.08, right=0.97, top=0.92, bottom=0.08)

# ── Panel A: ROC curve ────────────────────────────────────────────────────────
ax_roc = fig.add_subplot(gs[0, 0])
ax_roc.set_facecolor("white")
fpr, tpr, _ = roc_curve(all_labels, all_scores)
ax_roc.plot(fpr, tpr, color=BLUE, lw=2.2,
            label=f"PocketGNNXL  AUROC = {pooled_auroc:.4f}\n95% CI [{ci_lo:.4f}–{ci_hi:.4f}]")
ax_roc.fill_between(fpr, tpr, alpha=0.12, color=BLUE)
ax_roc.plot([0,1],[0,1], "--", color=GRAY, lw=1.0, label="Random (0.50)")
ax_roc.set_xlim(0, 1); ax_roc.set_ylim(0, 1.02)
ax_roc.set_xlabel("False Positive Rate", fontsize=9)
ax_roc.set_ylabel("True Positive Rate", fontsize=9)
ax_roc.set_title("A  ROC Curve — Held-Out Set", fontsize=10, fontweight="bold", loc="left")
ax_roc.legend(fontsize=7.5, framealpha=0.85, loc="lower right")
ax_roc.tick_params(labelsize=8)
ax_roc.spines[["top","right"]].set_visible(False)

# ── Panel B: PR curve ────────────────────────────────────────────────────────
ax_pr = fig.add_subplot(gs[0, 1])
ax_pr.set_facecolor("white")
prec, rec, _ = precision_recall_curve(all_labels, all_scores)
ax_pr.plot(rec, prec, color=RED, lw=2.2,
           label=f"PocketGNNXL  AUPRC = {pooled_auprc:.4f}\nLift = {pooled_auprc/trivial_auprc:.1f}× over random")
ax_pr.fill_between(rec, prec, alpha=0.12, color=RED)
ax_pr.axhline(trivial_auprc, color=GRAY, lw=1.0, ls="--",
              label=f"Random baseline = {trivial_auprc:.4f}")
ax_pr.set_xlim(0, 1); ax_pr.set_ylim(0, 1.02)
ax_pr.set_xlabel("Recall", fontsize=9)
ax_pr.set_ylabel("Precision", fontsize=9)
ax_pr.set_title("B  Precision–Recall Curve", fontsize=10, fontweight="bold", loc="left")
ax_pr.legend(fontsize=7.5, framealpha=0.85, loc="upper right")
ax_pr.tick_params(labelsize=8)
ax_pr.spines[["top","right"]].set_visible(False)

# ── Panel C: per-structure AUROC bar ─────────────────────────────────────────
ax_bar = fig.add_subplot(gs[1, 0])
ax_bar.set_facecolor("white")
sorted_ids = sorted(per_struct.keys(), key=lambda p: per_struct[p]["auroc"], reverse=True)
bar_aurocs = [per_struct[p]["auroc"] for p in sorted_ids]
bar_mccs   = [per_struct[p]["mcc"]   for p in sorted_ids]
bar_colors = [ORANGE if per_struct[p]["split"] == "val" else RED for p in sorted_ids]

x_pos = np.arange(len(sorted_ids))
bars = ax_bar.bar(x_pos, bar_aurocs, color=bar_colors, alpha=0.88,
                  edgecolor="white", linewidth=0.5, label="AUROC")
ax_bar.scatter(x_pos, bar_mccs, color=DARK, zorder=5, s=30,
               marker="D", label="MCC (optimal threshold)", alpha=0.9)

ax_bar.axhline(pooled_auroc, color=BLUE, lw=1.3, ls="--",
               label=f"Pooled AUROC = {pooled_auroc:.4f}")
ax_bar.axhline(0.5, color=GRAY, lw=0.8, ls=":", label="Random (0.5)")
ax_bar.set_xticks(x_pos)
ax_bar.set_xticklabels(sorted_ids, rotation=35, ha="right", fontsize=7.5)
ax_bar.set_ylim(0, 1.12)
ax_bar.set_ylabel("Score", fontsize=9)
ax_bar.set_title("C  Per-Structure AUROC & MCC", fontsize=10, fontweight="bold", loc="left")
ax_bar.legend(fontsize=7, framealpha=0.85, loc="lower left",
              handles=[
                  plt.Rectangle((0,0),1,1, color=ORANGE, alpha=0.88, label="Val set (n=8)"),
                  plt.Rectangle((0,0),1,1, color=RED,    alpha=0.88, label="Test set (n=5)"),
                  plt.Line2D([0],[0], color=BLUE, ls="--", lw=1.3, label=f"Pooled AUROC={pooled_auroc:.4f}"),
                  plt.Line2D([0],[0], marker="D", color=DARK, ls="", ms=5, label="MCC (opt. thr)"),
              ])
ax_bar.tick_params(labelsize=8)
ax_bar.spines[["top","right"]].set_visible(False)

# ── Panel D: Enrichment factor bar ───────────────────────────────────────────
ax_ef = fig.add_subplot(gs[1, 1])
ax_ef.set_facecolor("white")

ef_vals  = [per_struct[p]["ef1"] for p in sorted_ids]
ef5_vals = [per_struct[p]["ef5"] for p in sorted_ids]

x2 = np.arange(len(sorted_ids))
w  = 0.38
ax_ef.bar(x2 - w/2, ef_vals,  w, color=BLUE,  alpha=0.85, label="EF 1%")
ax_ef.bar(x2 + w/2, ef5_vals, w, color=GREEN, alpha=0.85, label="EF 5%")
ax_ef.axhline(1.0, color=GRAY, lw=1.0, ls="--", label="Random (EF=1×)")
ax_ef.axhline(pooled_ef1, color=BLUE, lw=1.1, ls=":",
              alpha=0.7, label=f"Pooled EF1% = {pooled_ef1:.1f}×")
ax_ef.axhline(pooled_ef5, color=GREEN, lw=1.1, ls=":",
              alpha=0.7, label=f"Pooled EF5% = {pooled_ef5:.1f}×")
ax_ef.set_xticks(x2)
ax_ef.set_xticklabels(sorted_ids, rotation=35, ha="right", fontsize=7.5)
ax_ef.set_ylabel("Enrichment Factor", fontsize=9)
ax_ef.set_title("D  Enrichment Factor (EF1% & EF5%)", fontsize=10, fontweight="bold", loc="left")
ax_ef.legend(fontsize=7, framealpha=0.85, loc="upper right")
ax_ef.tick_params(labelsize=8)
ax_ef.spines[["top","right"]].set_visible(False)

# ── super-title ───────────────────────────────────────────────────────────────
fig.suptitle(
    f"PocketGNNXL — Extended Validation Metrics\n"
    f"13 held-out CryptoSite proteins  |  "
    f"AUROC = {pooled_auroc:.4f}  |  MCC = {best_mcc_pooled:.4f}  |  "
    f"EF1% = {pooled_ef1:.1f}×  |  AUPRC lift = {pooled_auprc/trivial_auprc:.1f}×",
    fontsize=10.5, fontweight="bold", color=DARK, y=0.97,
)

fig.savefig(str(OUT_FIG), dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close(fig)
print(f"Figure saved: {OUT_FIG}")
