"""Generate full analysis figure and recompute AUROC with proper PCNA-chain filtering."""
import sys, csv, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models import PocketGNN
from src.data_processing.parse_pdb import parse_pdb, get_ligand_coords, label_pocket_residues
from src.data_processing.graph_construction import build_graph_v2
from sklearn.metrics import roc_auc_score
import torch

REPO  = Path(__file__).parent.parent
RAW   = REPO / "data" / "raw"
PDIR  = REPO / "results" / "per_structure"
CKPT  = REPO / "checkpoints" / "pcna" / "best_pcna.ckpt"
AOH_GT = {25,26,27,38,39,40,41,42,44,45,46,47,
           123,125,126,128,231,232,233,234,250,251,252,253}

# Ligands to skip: solvents, ions, replisome cofactors (belong to partner proteins)
SKIP = {
    'HOH','WAT','SO4','EDO','PEG','GOL','DMS','PO4','MPD','FMT','ACT',
    'MES','HED','BME','DTT','EPE','NHE','IMD','CIT','TRS','FLC','SCN',
    'AZI','NO3','PGE','PE5','PE7','NH4','ACE','MSE','SEP','TPO','PTR',
    'MG','CA','ZN','MN','FE','CU','NA','K','CD','AU','PT','CO','NI',
    'HG','SE','BR','CL','IOD',
    'AGS','ADP','ATP','GTP','GDP','TTP','TMP','DTP','SF4','FES','F3S',
    'DOC','APC','ANP','AMP','CTP','UTP','NAD','FAD','FMN',
}

rows = list(csv.DictReader(open(PDIR / "summary_table.csv", encoding="utf-8", errors="replace")))
pdbs = [r["pdb"] for r in rows]

# ── Re-compute AUROC: PCNA chains only + drug-like ligands only ───────────────
model = PocketGNN.small().eval()
model.load_state_dict(torch.load(CKPT, map_location="cpu", weights_only=True))

print("Re-computing AUROC (PCNA chains only, drug-like ligands only)...")
auroc_fixed = {}
for r in rows:
    pdb      = r["pdb"]
    pdb_path = RAW / f"{pdb}.pdb"
    if not pdb_path.exists():
        continue
    found = set()
    for line in pdb_path.read_text(errors="ignore").splitlines():
        if line.startswith("HETATM"):
            rn = line[17:20].strip()
            if rn not in SKIP:
                found.add(rn)
    if not found:
        continue
    try:
        residues = parse_pdb(pdb_path)
        data     = build_graph_v2(residues)
        chain_sizes = {}
        for res in residues:
            chain_sizes[res.chain] = chain_sizes.get(res.chain, 0) + 1
        pcna_chains = {c for c, n in chain_sizes.items() if 200 <= n <= 300}
        if not pcna_chains:
            pcna_chains = set(chain_sizes.keys())
        with torch.no_grad():
            scores = model(
                data.x, data.edge_index, data.edge_attr,
                data.edge_index_seq, data.edge_attr_seq,
                data.chain_id,
            ).numpy()
        all_lig = []
        for lig in found:
            coords = get_ligand_coords(pdb_path, resname=lig)
            if coords is not None:
                all_lig.append(coords)
        if not all_lig:
            continue
        lig_coords = np.vstack(all_lig)
        labels = label_pocket_residues(residues, lig_coords, cutoff_angstrom=6.0)
        mask   = np.array([res.chain in pcna_chains for res in residues])
        y_f    = labels[mask]
        s_f    = scores[mask]
        if y_f.sum() >= 2 and (1 - y_f).sum() >= 2:
            auroc = roc_auc_score(y_f, s_f)
            auroc_fixed[pdb] = auroc
            print(f"  {pdb:6s}: AUROC={auroc:.4f}  ligands={found}  "
                  f"pocket={int(y_f.sum())}  chains={pcna_chains}")
    except Exception as e:
        print(f"  {pdb}: ERROR {e}")

if auroc_fixed:
    vals = list(auroc_fixed.values())
    print(f"\nFixed AUROC: n={len(vals)}  mean={np.mean(vals):.4f}  "
          f"median={np.median(vals):.4f}  max={np.max(vals):.4f}")

# ── Figure ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(24, 20))
fig.suptitle("GNN-PCNA: Per-Structure Cryptic Pocket Analysis -- 59 PCNA Structures",
             fontsize=15, fontweight="bold", y=0.98)

top_means = [float(r["top_cluster_mean"]) for r in rows]
aoh_vals  = [int(r["top_aoh_overlap"])    for r in rows]
colors    = []
for r in rows:
    if r["pdb"] in {"8GLA", "8GL9", "8GCJ"}:
        colors.append("#e74c3c")
    elif r["pdb"] in {"1W60", "4RJF", "1U7B"}:
        colors.append("#3498db")
    elif r["pdb"] == "9B8T":
        colors.append("#9b59b6")
    else:
        colors.append("#95a5a6")

# Panel 1 — ranked bar + AOH dots
ax1 = fig.add_axes([0.04, 0.72, 0.92, 0.22])
ax1.bar(range(len(rows)), top_means, color=colors, width=0.8, linewidth=0)
ax2 = ax1.twinx()
ax2.plot(range(len(rows)), aoh_vals, "k.", markersize=4, alpha=0.6)
ax2.set_ylabel("AOH GT residues in top cluster", fontsize=8)
ax2.set_ylim(0, 28)
ax1.axhline(0.40, color="black", linewidth=1, linestyle="--", alpha=0.4)
ax1.set_xticks(range(len(rows)))
ax1.set_xticklabels(pdbs, rotation=90, fontsize=5.5)
ax1.set_ylabel("Top cluster mean score")
ax1.set_title("All 59 PCNA Structures -- Ranked by Pocket Score  (dots = AOH GT overlap count)")
ax1.set_ylim(0, 0.85)
legend_patches = [
    mpatches.Patch(color="#e74c3c", label="AOH1996 holo"),
    mpatches.Patch(color="#3498db", label="Canonical apo"),
    mpatches.Patch(color="#9b59b6", label="9B8T (novel site)"),
    mpatches.Patch(color="#95a5a6", label="Other PCNA"),
]
ax1.legend(handles=legend_patches, fontsize=7, loc="upper right")

# Panel 2 -- AUROC before vs after fix
ax3 = fig.add_axes([0.04, 0.40, 0.44, 0.26])
orig_d = {r["pdb"]: float(r["auroc"]) for r in rows if r["auroc"]}
common = sorted(set(orig_d) & set(auroc_fixed))
if common:
    c_col = ["#e74c3c" if p in {"8GLA","8GL9","8GCJ"} else "#3498db" for p in common]
    ax3.scatter([orig_d[p] for p in common], [auroc_fixed[p] for p in common],
                c=c_col, s=60, zorder=3)
    for p in common:
        ax3.annotate(p, (orig_d[p], auroc_fixed[p]), fontsize=6, ha="left", va="bottom")
    ax3.plot([0.3, 1], [0.3, 1], "k--", alpha=0.3, linewidth=1)
ax3.set_xlabel("Original AUROC (all chains, all ligands)")
ax3.set_ylabel("Fixed AUROC (PCNA chains, drug-like ligands only)")
ax3.set_title("AUROC Before vs After Labeling Correction")
ax3.set_xlim(0.3, 1.0)
ax3.set_ylim(0.3, 1.0)

# Panel 3 -- score vs AOH overlap
ax4 = fig.add_axes([0.54, 0.40, 0.42, 0.26])
pt_colors = ["#e74c3c" if r["pdb"] in {"8GLA","8GL9","8GCJ"}
             else "#9b59b6" if r["pdb"] == "9B8T"
             else "#3498db" if r["pdb"] in {"1W60","4RJF","1U7B"}
             else "#2ecc71" for r in rows]
ax4.scatter(top_means, aoh_vals, c=pt_colors, s=55, alpha=0.8)
for r in rows:
    if int(r["top_aoh_overlap"]) >= 20 or r["pdb"] == "9B8T":
        ax4.annotate(r["pdb"], (float(r["top_cluster_mean"]),
                     int(r["top_aoh_overlap"])), fontsize=6)
ax4.set_xlabel("Top cluster mean score")
ax4.set_ylabel("AOH1996 GT residues recovered")
ax4.set_title("Pocket Score vs Ground-Truth AOH1996 Recovery")

# Panel 4 -- score profiles 8GLA vs 9B8T vs 1W60
ax5 = fig.add_axes([0.04, 0.06, 0.44, 0.28])
for pdb_id, color, label in [
    ("8GLA", "#e74c3c", "8GLA (AOH1996 holo)"),
    ("9B8T", "#9b59b6", "9B8T (Pol epsilon + DNA -- novel site)"),
    ("1W60", "#3498db", "1W60 (apo)"),
]:
    try:
        sc_df = list(csv.DictReader(
            open(PDIR / pdb_id / "scores.csv", encoding="utf-8", errors="replace")))
        # Use first two unique chains (PCNA chains) regardless of letter
        chains_present = list(dict.fromkeys(r["chain"] for r in sc_df))
        use_chains = set(chains_present[:2])
        resids  = [int(r["resid"])   for r in sc_df if r["chain"] in use_chains]
        scores_ = [float(r["score"]) for r in sc_df if r["chain"] in use_chains]
        ax5.plot(resids, scores_, color=color, linewidth=0.8, alpha=0.85, label=label)
    except Exception as e:
        print(f"  profile error {pdb_id}: {e}")
for rid in AOH_GT:
    ax5.axvspan(rid - 0.5, rid + 0.5, color="red", alpha=0.07)
ax5.axhline(0.40, color="k", linewidth=0.8, linestyle="--", alpha=0.5)
ax5.set_xlabel("Residue ID")
ax5.set_ylabel("Pocket score")
ax5.set_title("Score Profiles: 8GLA vs 9B8T vs 1W60\n(red shading = AOH1996 GT pocket region)")
ax5.legend(fontsize=7)
ax5.set_ylim(0, 1)

# Panel 5 -- AUROC distribution (fixed)
ax6 = fig.add_axes([0.54, 0.06, 0.42, 0.28])
if auroc_fixed:
    all_fixed = list(auroc_fixed.values())
    ax6.hist(all_fixed, bins=10, color="#2ecc71", edgecolor="white", linewidth=0.5)
    ax6.axvline(np.mean(all_fixed), color="red", linewidth=1.5,
                linestyle="--", label=f"Mean = {np.mean(all_fixed):.3f}")
    ax6.axvline(0.5, color="gray", linewidth=1,
                linestyle=":", label="Random (0.5)")
    ax6.set_xlabel("AUROC")
    ax6.set_ylabel("Number of structures")
    ax6.set_title("AUROC Distribution\n(PCNA-chain filtered, drug-like ligands only)")
    ax6.legend(fontsize=8)

out = PDIR / "full_analysis.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"\nSaved: {out}")
