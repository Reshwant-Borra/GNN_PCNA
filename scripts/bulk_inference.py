"""
Bulk inference on all PDB structures in data/raw/.
Outputs:
  results/bulk_inference/scores.csv      — per-structure summary
  results/bulk_inference/clusters.csv    — top DBSCAN cluster per structure
  results/bulk_inference/profiles.png    — score profiles for top 20 structures
  results/bulk_inference/ranked.png      — all structures ranked by pocket evidence
"""
from __future__ import annotations
import sys, json, warnings
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.models import PocketGNN
from src.data_processing.parse_pdb import parse_pdb
from src.data_processing.graph_construction import build_graph_v2

THRESHOLD  = 0.40
CKPT       = REPO_ROOT / "checkpoints" / "pcna" / "best_pcna.ckpt"
RAW_DIR    = REPO_ROOT / "data" / "raw"
OUT_DIR    = REPO_ROOT / "results" / "bulk_inference"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Known reference structures
HOLO_IDS = {"8GLA", "8GL9", "8GCJ"}          # AOH1996-bound
APO_IDS  = {"1W60", "4RJF", "1U7B"}  # canonical apo — 1W61 removed (proline racemase, not PCNA)

GT_RESIDS = {25,26,27,38,39,40,41,42,44,45,46,47,
             123,125,126,128,231,232,233,234,250,251,252,253}


def cluster_pockets(residues, scores, threshold=THRESHOLD):
    from sklearn.cluster import DBSCAN
    high = np.where(scores >= threshold)[0]
    if len(high) < 3:
        return []
    coords = np.array([residues[i].ca_coord for i in high])
    labels = DBSCAN(eps=6.0, min_samples=3).fit(coords).labels_
    pockets = []
    for cid in sorted(set(labels)):
        if cid == -1:
            continue
        idx = high[labels == cid]
        sc  = scores[idx]
        pockets.append({
            "n_residues": len(idx),
            "mean_score": float(sc.mean()),
            "max_score" : float(sc.max()),
            "center"    : np.array([residues[i].ca_coord for i in idx]).mean(0).tolist(),
            "resids"    : [residues[i].resid for i in idx],
            "chains"    : [residues[i].chain for i in idx],
        })
    pockets.sort(key=lambda p: p["mean_score"] * p["n_residues"]**0.5, reverse=True)
    return pockets


def run_one(pdb_path: Path, model: torch.nn.Module) -> dict | None:
    try:
        residues = parse_pdb(pdb_path)
        if len(residues) < 20:
            return None
        data = build_graph_v2(residues)
        with torch.no_grad():
            scores = model(
                data.x, data.edge_index, data.edge_attr,
                data.edge_index_seq, data.edge_attr_seq,
                data.chain_id,
            ).numpy()
        pockets = cluster_pockets(residues, scores)
        chains  = sorted(set(r.chain for r in residues))

        # GT overlap (chain-agnostic — check resid only)
        top30_resids = {residues[i].resid for i in np.argsort(scores)[-30:]}
        gt_hits = len(top30_resids & GT_RESIDS)

        return {
            "pdb"          : pdb_path.stem,
            "n_residues"   : len(residues),
            "n_chains"     : len(chains),
            "chains"       : ",".join(chains),
            "max_score"    : float(scores.max()),
            "mean_score"   : float(scores.mean()),
            "n_above_thr"  : int((scores >= THRESHOLD).sum()),
            "n_clusters"   : len(pockets),
            "top_cluster_n": pockets[0]["n_residues"]   if pockets else 0,
            "top_cluster_mean": pockets[0]["mean_score"] if pockets else 0.0,
            "top_cluster_max" : pockets[0]["max_score"]  if pockets else 0.0,
            "gt_hits_top30": gt_hits,
            "residues"     : residues,
            "scores"       : scores,
            "pockets"      : pockets,
        }
    except Exception as e:
        warnings.warn(f"{pdb_path.stem}: {e}")
        return None


def make_ranked_plot(rows: list[dict]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    rows_s = sorted(rows, key=lambda r: r["top_cluster_mean"], reverse=True)
    labels = [r["pdb"] for r in rows_s]
    vals   = [r["top_cluster_mean"] for r in rows_s]
    colors = []
    for r in rows_s:
        if r["pdb"] in HOLO_IDS:
            colors.append("#e74c3c")
        elif r["pdb"] in APO_IDS:
            colors.append("#3498db")
        else:
            colors.append("#95a5a6")

    fig, ax = plt.subplots(figsize=(22, 6))
    bars = ax.bar(range(len(labels)), vals, color=colors, width=0.8, linewidth=0)
    ax.axhline(THRESHOLD, color="black", linewidth=1.0, linestyle="--", alpha=0.5,
               label=f"Threshold ({THRESHOLD})")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, fontsize=5.5)
    ax.set_ylabel("Top cluster mean score")
    ax.set_title("PCNA Structures — Ranked by Cryptic Pocket Evidence", fontsize=13, fontweight="bold")
    ax.set_xlim(-0.5, len(labels) - 0.5)
    ax.set_ylim(0, 1.05)
    legend_patches = [
        mpatches.Patch(color="#e74c3c", label="Known holo (AOH1996-bound)"),
        mpatches.Patch(color="#3498db", label="Known apo"),
        mpatches.Patch(color="#95a5a6", label="Other structures"),
    ]
    ax.legend(handles=legend_patches + [
        plt.Line2D([0],[0], color="black", linestyle="--", label=f"Threshold {THRESHOLD}")
    ], fontsize=8)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "ranked.png", dpi=160)
    plt.close(fig)
    print(f"  Saved: {OUT_DIR/'ranked.png'}")


def make_profiles_plot(rows: list[dict], n: int = 20) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    top = sorted(rows, key=lambda r: r["top_cluster_mean"], reverse=True)[:n]
    ncols = 4
    nrows = (len(top) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(22, 3.5 * nrows))
    axes = axes.flatten()

    for ax, r in zip(axes, top):
        residues = r["residues"]
        scores   = r["scores"]
        resids   = np.array([res.resid for res in residues])
        chains   = [res.chain for res in residues]
        unique_ch = sorted(set(chains))

        for ch in unique_ch:
            mask = np.array([c == ch for c in chains])
            ax.plot(resids[mask], scores[mask], linewidth=0.8, alpha=0.85, label=f"Chain {ch}")

        ax.axhline(THRESHOLD, color="black", linewidth=0.8, linestyle="--", alpha=0.6)

        # shade GT residue positions
        for rid in GT_RESIDS:
            ax.axvspan(rid - 0.5, rid + 0.5, color="red", alpha=0.08)

        tag = ""
        if r["pdb"] in HOLO_IDS: tag = " [HOLO]"
        elif r["pdb"] in APO_IDS: tag = " [APO]"
        ax.set_title(f"{r['pdb']}{tag}  clusters={r['n_clusters']}  "
                     f"top={r['top_cluster_mean']:.3f}", fontsize=8, fontweight="bold")
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("Residue ID", fontsize=7)
        ax.set_ylabel("Score", fontsize=7)
        ax.tick_params(labelsize=6)
        ax.legend(fontsize=5, loc="upper right")

    for ax in axes[len(top):]:
        ax.set_visible(False)

    fig.suptitle("Top-20 PCNA Structures — Score Profiles\n(red shading = AOH1996 GT pocket region)",
                 fontsize=12, fontweight="bold")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "profiles.png", dpi=150)
    plt.close(fig)
    print(f"  Saved: {OUT_DIR/'profiles.png'}")


def main():
    print(f"Loading checkpoint: {CKPT}")
    model = PocketGNN.small().eval()
    model.load_state_dict(torch.load(CKPT, map_location="cpu", weights_only=True))

    pdb_files = sorted(RAW_DIR.glob("*.pdb"))
    print(f"Found {len(pdb_files)} PDB files in {RAW_DIR}\n")

    rows = []
    failed = []
    for pdb_path in tqdm(pdb_files, desc="Inference", ncols=90):
        result = run_one(pdb_path, model)
        if result:
            rows.append(result)
        else:
            failed.append(pdb_path.stem)

    print(f"\nProcessed {len(rows)}/{len(pdb_files)}  ({len(failed)} failed)")
    if failed:
        print(f"  Failed: {', '.join(failed)}")

    # ── save scores CSV ───────────────────────────────────────────────────────
    import csv
    csv_cols = ["pdb","n_residues","n_chains","chains","max_score","mean_score",
                "n_above_thr","n_clusters","top_cluster_n","top_cluster_mean",
                "top_cluster_max","gt_hits_top30"]
    with open(OUT_DIR / "scores.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=csv_cols)
        w.writeheader()
        for r in sorted(rows, key=lambda x: x["top_cluster_mean"], reverse=True):
            w.writerow({k: r[k] for k in csv_cols})
    print(f"  Saved: {OUT_DIR/'scores.csv'}")

    # ── save clusters CSV ─────────────────────────────────────────────────────
    with open(OUT_DIR / "clusters.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pdb","rank","n_residues","mean_score","max_score",
                    "center_x","center_y","center_z","gt_hits"])
        for r in sorted(rows, key=lambda x: x["top_cluster_mean"], reverse=True):
            for i, p in enumerate(r["pockets"], 1):
                gt_hits = len(set(p["resids"]) & GT_RESIDS)
                cx,cy,cz = p["center"]
                w.writerow([r["pdb"], i, p["n_residues"],
                            round(p["mean_score"],4), round(p["max_score"],4),
                            round(cx,1), round(cy,1), round(cz,1), gt_hits])
    print(f"  Saved: {OUT_DIR/'clusters.csv'}")

    # ── print top 25 ─────────────────────────────────────────────────────────
    ranked = sorted(rows, key=lambda x: x["top_cluster_mean"], reverse=True)
    print(f"\n{'Rank':>4} {'PDB':>6} {'Res':>5} {'Ch':>3} {'Clusters':>8} "
          f"{'TopMean':>8} {'TopMax':>7} {'GT@30':>6}  {'Note'}")
    print("-" * 80)
    for i, r in enumerate(ranked[:25], 1):
        note = ""
        if r["pdb"] in HOLO_IDS: note = "<-- known HOLO"
        elif r["pdb"] in APO_IDS: note = "<-- known APO"
        print(f"{i:4d} {r['pdb']:>6} {r['n_residues']:5d} {r['n_chains']:3d} "
              f"{r['n_clusters']:8d} {r['top_cluster_mean']:8.4f} "
              f"{r['top_cluster_max']:7.4f} {r['gt_hits_top30']:6d}  {note}")

    # ── plots ─────────────────────────────────────────────────────────────────
    print("\nGenerating plots...")
    make_ranked_plot(rows)
    make_profiles_plot(rows, n=20)
    print("\nDone.")


if __name__ == "__main__":
    main()
