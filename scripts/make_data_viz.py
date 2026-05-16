"""
Comprehensive visualization of all GNN-PCNA computed data.

Panels:
  A  V1 vs V3 AUROC — horizontal bar chart for drug-like ligand structures
  B  Score distributions — violin plot across all 59 structures (v3 max score)
  C  AOH pocket recovery — heatmap of residue-level predictions on 8GLA chains A/B/C
  D  Top cluster score vs AOH overlap — scatter coloured by structure type
  E  Per-residue score profiles — 8GLA chain A (v1 vs v3, GT highlighted)
  F  All-structure overview — top-cluster score vs n_residues, coloured by AUROC

Output: results/figures/data_visualization.png  (300 dpi)
"""
import sys, io, csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.patches as mpatches

REPO   = Path(__file__).parent.parent
V3_DIR = REPO / "results" / "v3"
V1_DIR = REPO / "results" / "per_structure"
FIG_DIR = REPO / "results" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

AOH_GT = {25,26,27,38,39,40,41,42,44,45,46,47,
           123,125,126,128,231,232,233,234,250,251,252,253}

# ── load summaries ────────────────────────────────────────────────────────────
v3_rows = list(csv.DictReader(open(V3_DIR / "v3_summary.csv", encoding="utf-8")))
v1_rows = list(csv.DictReader(open(V1_DIR / "summary_table.csv",
                                   encoding="utf-8", errors="replace")))

v1_map = {r["pdb"]: r for r in v1_rows}

def flt(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

# Build merged table
data = []
for r in v3_rows:
    pdb  = r["pdb"]
    v1   = v1_map.get(pdb, {})
    data.append({
        "pdb"          : pdb,
        "n_residues"   : int(r["n_residues"]),
        "n_chains"     : int(v1.get("n_chains", 0) or 0),
        "auroc_v3"     : flt(r["auroc_v3"]),
        "auroc_v1"     : flt(v1.get("auroc")),
        "top_score_v3" : flt(r["top_cluster_mean"]),
        "top_score_v1" : flt(v1.get("top_cluster_mean")),
        "top_n_v3"     : int(r["top_cluster_n"]),
        "aoh_v3"       : int(r["top_aoh_overlap"]),
        "aoh_v1"       : int(v1.get("top_aoh_overlap", 0) or 0),
        "score_max_v3" : flt(r["score_max"]),
        "score_mean_v3": flt(r["score_mean"]),
        "score_max_v1" : flt(v1.get("score_max")),
        "concavity"    : flt(v1.get("top_concavity")),
        "ligands"      : v1.get("ligands", ""),
    })

# Structures with drug-like ligand AUROC
auroc_structs = [d for d in data if d["auroc_v3"] is not None and d["auroc_v1"] is not None]
auroc_structs.sort(key=lambda x: x["auroc_v3"])

# ── figure layout ─────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(22, 26))
gs  = gridspec.GridSpec(3, 2, figure=fig,
                        hspace=0.42, wspace=0.32,
                        left=0.07, right=0.97, top=0.94, bottom=0.05)

BLUE   = "#4472C4"
ORANGE = "#ED7D31"
GREEN  = "#70AD47"
RED    = "#FF5252"
GREY   = "#BDBDBD"

# ── Panel A: V1 vs V3 AUROC bar chart ─────────────────────────────────────────
ax_a = fig.add_subplot(gs[0, 0])
labels = [d["pdb"] for d in auroc_structs]
v1_vals = [d["auroc_v1"] for d in auroc_structs]
v3_vals = [d["auroc_v3"] for d in auroc_structs]
y = np.arange(len(labels))
h = 0.35
bars1 = ax_a.barh(y + h/2, v1_vals, h, label="V1 (~907k, hand-crafted)", color=BLUE,  alpha=0.85)
bars2 = ax_a.barh(y - h/2, v3_vals, h, label="V3 (13.4M + ESM2)",        color=ORANGE, alpha=0.85)
ax_a.set_yticks(y)
ax_a.set_yticklabels(labels, fontsize=9)
ax_a.axvline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
ax_a.axvline(0.8, color="gray", linestyle=":",  linewidth=0.8, alpha=0.5)
ax_a.set_xlim(0, 1.08)
ax_a.set_xlabel("AUROC", fontsize=10)
ax_a.set_title("A  |  V1 vs V3 AUROC — drug-like ligand structures", fontsize=11, fontweight="bold", pad=6)
ax_a.legend(fontsize=8, loc="lower right")
# Delta labels
for i, (v1, v3) in enumerate(zip(v1_vals, v3_vals)):
    delta = v3 - v1
    ax_a.text(max(v1, v3) + 0.01, i, f"+{delta:.3f}", va="center", fontsize=7.5,
              color=GREEN if delta > 0.1 else "black", fontweight="bold" if delta > 0.2 else "normal")
ax_a.spines["top"].set_visible(False)
ax_a.spines["right"].set_visible(False)

# ── Panel B: Max score distribution violin — all 59 structures ─────────────────
ax_b = fig.add_subplot(gs[0, 1])
# Group by AOH overlap tier
tier_high  = [d for d in data if d["aoh_v3"] >= 20]
tier_mid   = [d for d in data if 4 <= d["aoh_v3"] < 20]
tier_low   = [d for d in data if d["aoh_v3"] < 4]

groups = [
    ([d["score_max_v3"] for d in tier_high if d["score_max_v3"]], "AOH>=20/24\n(n=%d)" % len(tier_high), GREEN),
    ([d["score_max_v3"] for d in tier_mid  if d["score_max_v3"]], "AOH 4-19/24\n(n=%d)" % len(tier_mid),  ORANGE),
    ([d["score_max_v3"] for d in tier_low  if d["score_max_v3"]], "AOH 0-3/24\n(n=%d)" % len(tier_low),   BLUE),
]
positions = [1, 2, 3]
for pos, (vals, lbl, col) in zip(positions, groups):
    if vals:
        vp = ax_b.violinplot(vals, positions=[pos], widths=0.6, showmedians=True,
                             showextrema=True)
        for body in vp["bodies"]:
            body.set_facecolor(col)
            body.set_alpha(0.7)
        vp["cmedians"].set_color("white")
        vp["cmedians"].set_linewidth(2)
        ax_b.scatter([pos + np.random.uniform(-0.12, 0.12) for _ in vals], vals,
                     s=20, color=col, alpha=0.6, zorder=3, edgecolors="none")
ax_b.set_xticks(positions)
ax_b.set_xticklabels([g[1] for g in groups], fontsize=9)
ax_b.axhline(0.4, color="red", linestyle="--", linewidth=0.9, alpha=0.7, label="Threshold 0.40")
ax_b.set_ylabel("Max score (V3)", fontsize=10)
ax_b.set_ylim(0, 1.05)
ax_b.set_title("B  |  V3 max score distribution by AOH pocket recovery tier",
               fontsize=11, fontweight="bold", pad=6)
ax_b.legend(fontsize=8, loc="lower right")
ax_b.spines["top"].set_visible(False)
ax_b.spines["right"].set_visible(False)

# ── Panel C: 8GLA per-residue score profile — V1 vs V3 with GT ───────────────
ax_c = fig.add_subplot(gs[1, :])
# Load 8GLA per-residue scores
def load_scores(path):
    if not path.exists():
        return {}
    rows = list(csv.DictReader(open(path, encoding="utf-8", errors="replace")))
    return {(r["chain"], int(r["resid"])): float(r["score"]) for r in rows}

v3_scores_8gla = load_scores(V3_DIR / "8GLA" / "scores.csv")
v1_scores_8gla = load_scores(V1_DIR / "8GLA" / "scores.csv")

# Chain A residue list from v3
chain_a_keys = sorted([(ch, ri) for (ch, ri) in v3_scores_8gla if ch == "A"])
resids_a = [ri for _, ri in chain_a_keys]
v3_a = np.array([v3_scores_8gla[(ch, ri)] for ch, ri in chain_a_keys])
v1_a = np.array([v1_scores_8gla.get(("A", ri), 0.0) for _, ri in chain_a_keys])
gt_mask = np.array([ri in AOH_GT for ri in resids_a])
x_pos = np.arange(len(resids_a))

ax_c.fill_between(x_pos, 0, v3_a, alpha=0.35, color=ORANGE, label="V3 score")
ax_c.fill_between(x_pos, 0, v1_a, alpha=0.35, color=BLUE,   label="V1 score")
ax_c.plot(x_pos, v3_a, linewidth=0.8, color=ORANGE, alpha=0.9)
ax_c.plot(x_pos, v1_a, linewidth=0.8, color=BLUE,   alpha=0.9)
# GT residue markers
gt_x = x_pos[gt_mask]
ax_c.scatter(gt_x, np.ones(gt_mask.sum()) * 1.01, marker="|", s=80,
             color=RED, linewidths=1.5, zorder=5, label="AOH1996 GT residue")
ax_c.axhline(0.40, color="gray", linestyle="--", linewidth=0.9, alpha=0.7, label="Threshold 0.40")
ax_c.set_xlim(-1, len(resids_a))
ax_c.set_ylim(0, 1.1)

# x-tick every 10 residues
step = 10
tick_pos = x_pos[::step]
tick_lbl = [str(resids_a[i]) for i in range(0, len(resids_a), step)]
ax_c.set_xticks(tick_pos)
ax_c.set_xticklabels(tick_lbl, fontsize=7, rotation=45)
ax_c.set_xlabel("Residue ID — 8GLA Chain A", fontsize=10)
ax_c.set_ylabel("Pocket probability", fontsize=10)
ax_c.set_title("C  |  8GLA Chain A score profile — V1 vs V3 with AOH1996 ground truth",
               fontsize=11, fontweight="bold", pad=6)
ax_c.legend(fontsize=8, loc="upper left", ncol=4)
ax_c.spines["top"].set_visible(False)
ax_c.spines["right"].set_visible(False)

# Annotate key AOH regions
for label, resid_range in [("IDCL\n(123-128)", (123, 128)),
                             ("C-term\n(231-234)", (231, 234)),
                             ("N-face\n(25-27)", (25, 27))]:
    r_start, r_end = resid_range
    xi = [i for i, ri in enumerate(resids_a) if r_start <= ri <= r_end]
    if xi:
        xm = np.mean(xi)
        ax_c.annotate(label, xy=(xm, 0.97), fontsize=7, ha="center",
                      color=RED, fontweight="bold",
                      xytext=(xm, 0.97), textcoords="data")

# ── Panel D: Top cluster score vs AOH overlap scatter ────────────────────────
ax_d = fig.add_subplot(gs[2, 0])
aoh_vals   = np.array([d["aoh_v3"]       for d in data])
tscore_v3  = np.array([d["top_score_v3"] for d in data if d["top_score_v3"]])
aoh_for_ts = np.array([d["aoh_v3"]       for d in data if d["top_score_v3"]])
auroc_for_ts = np.array([d["auroc_v3"] if d["auroc_v3"] is not None else np.nan
                          for d in data if d["top_score_v3"]])
has_auroc_mask = ~np.isnan(auroc_for_ts)

sc = ax_d.scatter(aoh_for_ts[~has_auroc_mask], tscore_v3[~has_auroc_mask],
                  s=50, color=GREY, alpha=0.6, zorder=2, label="No drug-like ligand")
sc2 = ax_d.scatter(aoh_for_ts[has_auroc_mask], tscore_v3[has_auroc_mask],
                   c=auroc_for_ts[has_auroc_mask],
                   s=120, cmap="RdYlGn", vmin=0.5, vmax=1.0,
                   edgecolors="black", linewidths=0.5, zorder=3, label="Has AUROC")
cb = fig.colorbar(sc2, ax=ax_d, shrink=0.8, pad=0.02)
cb.set_label("AUROC (V3)", fontsize=8)
# Label key structures
for d in data:
    if d["pdb"] in {"8GLA", "3VKX", "9N3L", "8GL9", "6CBI", "9B8T"} and d["top_score_v3"]:
        ax_d.annotate(d["pdb"], (d["aoh_v3"], d["top_score_v3"]),
                      fontsize=7.5, ha="left", va="bottom",
                      xytext=(3, 3), textcoords="offset points")
ax_d.set_xlabel("AOH1996 GT residues in top cluster (/24)", fontsize=10)
ax_d.set_ylabel("Top cluster mean score (V3)", fontsize=10)
ax_d.set_title("D  |  AOH overlap vs top cluster score (V3)", fontsize=11, fontweight="bold", pad=6)
ax_d.legend(fontsize=8, loc="lower right")
ax_d.spines["top"].set_visible(False)
ax_d.spines["right"].set_visible(False)

# ── Panel E: V1 vs V3 top cluster score comparison — all 59 structures ───────
ax_e = fig.add_subplot(gs[2, 1])
ts_v1  = np.array([d["top_score_v1"] for d in data if d["top_score_v1"] and d["top_score_v3"]])
ts_v3  = np.array([d["top_score_v3"] for d in data if d["top_score_v1"] and d["top_score_v3"]])
aoh_e  = np.array([d["aoh_v3"]       for d in data if d["top_score_v1"] and d["top_score_v3"]])
pdbs_e = [d["pdb"]                    for d in data if d["top_score_v1"] and d["top_score_v3"]]

cmap_e = plt.cm.RdYlGn
norm_e = Normalize(vmin=0, vmax=24)
colors_e = cmap_e(norm_e(aoh_e))

ax_e.scatter(ts_v1, ts_v3, c=colors_e, s=60, edgecolors="black", linewidths=0.4, zorder=3)
# Diagonal
lim = (0.55, 1.0)
ax_e.plot(lim, lim, "k--", linewidth=0.8, alpha=0.5, label="V1 = V3")
ax_e.fill_between(lim, lim, [1.0, 1.0], alpha=0.04, color=ORANGE)
ax_e.text(0.85, 0.95, "V3 wins", fontsize=8, color=ORANGE, alpha=0.8)
# Label selected structures
for pdb, v1s, v3s in zip(pdbs_e, ts_v1, ts_v3):
    if pdb in {"8GLA", "6CBI", "3VKX", "9B8T", "8GL9"}:
        ax_e.annotate(pdb, (v1s, v3s), fontsize=7.5,
                      xytext=(4, -8), textcoords="offset points")
sm = ScalarMappable(cmap=cmap_e, norm=norm_e)
sm.set_array([])
cb2 = fig.colorbar(sm, ax=ax_e, shrink=0.8, pad=0.02)
cb2.set_label("AOH overlap /24", fontsize=8)
ax_e.set_xlim(*lim)
ax_e.set_ylim(*lim)
ax_e.set_xlabel("V1 top cluster mean score", fontsize=10)
ax_e.set_ylabel("V3 top cluster mean score", fontsize=10)
ax_e.set_title("E  |  Top cluster score: V1 vs V3 (all 59 structures)", fontsize=11, fontweight="bold", pad=6)
ax_e.legend(fontsize=8)
ax_e.spines["top"].set_visible(False)
ax_e.spines["right"].set_visible(False)

# ── title + stats block ────────────────────────────────────────────────────────
n_auroc   = sum(1 for d in data if d["auroc_v3"] is not None)
mean_v3   = np.mean([d["auroc_v3"] for d in data if d["auroc_v3"] is not None])
mean_v1   = np.mean([d["auroc_v1"] for d in data if d["auroc_v1"] is not None and d["auroc_v3"] is not None])
n_full    = sum(1 for d in data if d["aoh_v3"] == 24)
n_good    = sum(1 for d in data if d["aoh_v3"] >= 20)

fig.suptitle(
    "GNN-PCNA: PocketGNNXL V3 vs PocketGNN V1 — Comprehensive Data Summary\n"
    f"{len(data)} PCNA structures  |  "
    f"{n_auroc} with drug-like AUROC  |  "
    f"V3 mean AUROC: {mean_v3:.4f}  (V1: {mean_v1:.4f})  |  "
    f"{n_full} structures with 24/24 AOH overlap  |  {n_good} with >=20/24",
    fontsize=12, fontweight="bold", y=0.975,
)

out = FIG_DIR / "data_visualization.png"
fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved -> {out}")
print(f"  {len(data)} structures  |  {n_auroc} AUROC  |  V3 mean={mean_v3:.4f}  V1 mean={mean_v1:.4f}")
