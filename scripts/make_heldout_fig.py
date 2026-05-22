"""
Regenerate Fig 3 as a held-out-only AUROC bar chart.
Uses data already in all_structures_scores.csv + cryptosite_split.json.
No model inference needed.
"""
import json, csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

REPO    = Path(__file__).parent.parent
OUT     = REPO / "data" / "results" / "fig3_cryptosite_histograms.png"

split   = json.loads((REPO / "data/splits/cryptosite_split.json").read_text())["splits"]
VAL     = set(split["val"])
TEST    = set(split["test"])
HELD    = VAL | TEST

rows    = list(csv.DictReader(open(REPO / "data/results/all_structures_scores.csv")))
held    = [r for r in rows if r["pdb_id"] in HELD and r["auroc"] not in ("", "nan")]
held    = sorted(held, key=lambda r: float(r["auroc"]), reverse=True)

pdbs    = [r["pdb_id"]       for r in held]
aurocs  = [float(r["auroc"]) for r in held]
colors  = ["#E84646" if p in TEST else "#F5A623" for p in pdbs]
mean_auroc = np.mean(aurocs)

fig, ax = plt.subplots(figsize=(7.2, 3.6))
bars = ax.bar(pdbs, aurocs, color=colors, alpha=0.88, edgecolor="white", linewidth=0.5)

ax.axhline(mean_auroc, color="black", lw=1.2, ls="--",
           label=f"Mean AUROC = {mean_auroc:.4f}")
ax.axhline(0.5, color="gray", lw=0.8, ls=":", label="Random baseline (0.5)")

# annotate each bar
for bar, auroc in zip(bars, aurocs):
    ax.text(bar.get_x() + bar.get_width()/2, auroc + 0.012,
            f"{auroc:.3f}", ha="center", va="bottom", fontsize=7.5, fontweight="bold")

ax.set_ylim(0, 1.08)
ax.set_ylabel("AUROC", fontsize=9)
ax.set_xlabel("CryptoSite structure (held-out only)", fontsize=9)
ax.set_title("PocketGNNXL — Held-Out Generalization\n"
             "Val (8) + Test (5) CryptoSite proteins  |  Never seen during training or fine-tuning",
             fontsize=9)
ax.tick_params(axis="x", labelsize=8, rotation=30)
ax.tick_params(axis="y", labelsize=8)

legend_patches = [
    mpatches.Patch(color="#F5A623", alpha=0.88, label="Validation set (n=8)"),
    mpatches.Patch(color="#E84646", alpha=0.88, label="Test set (n=5)"),
    plt.Line2D([0],[0], color="black", ls="--", lw=1.2, label=f"Mean AUROC = {mean_auroc:.4f}"),
    plt.Line2D([0],[0], color="gray",  ls=":",  lw=0.8, label="Random baseline (0.5)"),
]
ax.legend(handles=legend_patches, fontsize=7.5, loc="lower left", framealpha=0.85)

fig.tight_layout()
fig.savefig(OUT, dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Saved {OUT.name}  (n={len(held)}, mean AUROC={mean_auroc:.4f})")
