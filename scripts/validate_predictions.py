"""
Prediction validator for PocketGNN bulk inference results.

Three independent checks run per structure:
  1. MC Dropout uncertainty  — run forward pass N times with dropout ON,
                               measure per-residue std. High std = model unsure.
  2. Trimer symmetry check   — for 3-chain structures, correlate scores across
                               chains. Low correlation = inconsistent = suspicious.
  3. Geometric concavity     — check whether the predicted cluster center sits in
                               a concave region or on a convex surface. Uses the
                               inward-pointing neighbor test on Cα coordinates.

Outputs:
  results/validation/validated_scores.csv   — re-ranked with confidence columns
  results/validation/confidence.png         — scatter: raw score vs confidence
  results/validation/flags.txt              — structures flagged as unreliable
"""
from __future__ import annotations
import sys, csv, warnings
from pathlib import Path

import numpy as np
import torch
from tqdm import tqdm

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.models import PocketGNN
from src.data_processing.parse_pdb import parse_pdb
from src.data_processing.graph_construction import build_graph_v2

CKPT      = REPO_ROOT / "checkpoints" / "pcna" / "best_pcna.ckpt"
RAW_DIR   = REPO_ROOT / "data" / "raw"
IN_CSV    = REPO_ROOT / "results" / "bulk_inference" / "scores.csv"
OUT_DIR   = REPO_ROOT / "results" / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MC_RUNS   = 50      # forward passes for uncertainty estimate
THRESHOLD = 0.40


# ── MC Dropout uncertainty ────────────────────────────────────────────────────

def mc_dropout_uncertainty(model: torch.nn.Module, data,
                           n_runs: int = MC_RUNS) -> tuple[np.ndarray, np.ndarray]:
    """
    Enable dropout during inference and run N forward passes.
    Returns (mean_scores, std_scores) — std is the epistemic uncertainty.
    High std means the model is not confident about that residue.
    """
    model.train()  # activates dropout layers
    all_scores = []
    with torch.no_grad():
        for _ in range(n_runs):
            s = model(
                data.x, data.edge_index, data.edge_attr,
                data.edge_index_seq, data.edge_attr_seq,
                data.chain_id,
            ).numpy()
            all_scores.append(s)
    model.eval()
    stack = np.stack(all_scores)          # (n_runs, N)
    return stack.mean(0), stack.std(0)    # (N,), (N,)


# ── Trimer symmetry consistency ───────────────────────────────────────────────

def trimer_symmetry_score(scores: np.ndarray, chain_id: torch.Tensor,
                          n_chains: int) -> float:
    """
    For homotrimers, scores on chains A/B/C should be similar (same sequence,
    same fold). Compute mean pairwise Pearson correlation across chains.
    Returns value in [-1, 1]. Values below 0.5 = suspicious asymmetry.
    Returns None if fewer than 2 chains have enough residues to compare.
    """
    chain_scores = []
    for ci in range(n_chains):
        mask = (chain_id == ci).numpy()
        if mask.sum() >= 20:
            chain_scores.append(scores[mask])

    if len(chain_scores) < 2:
        return None

    # Pad/trim to common length for correlation
    min_len = min(len(s) for s in chain_scores)
    chain_scores = [s[:min_len] for s in chain_scores]

    corrs = []
    for i in range(len(chain_scores)):
        for j in range(i + 1, len(chain_scores)):
            a, b = chain_scores[i], chain_scores[j]
            if a.std() > 0 and b.std() > 0:
                corrs.append(float(np.corrcoef(a, b)[0, 1]))

    return float(np.mean(corrs)) if corrs else None


# ── Geometric concavity ───────────────────────────────────────────────────────

def concavity_score(residues, cluster_residue_idxs: np.ndarray) -> float:
    """
    Test whether predicted pocket residues sit in a concave region.

    Method: for each pocket residue, compute the vector from the protein
    centroid to that residue (outward-pointing). Then check how many of its
    spatial neighbors lie *further* from the centroid (i.e., are more exposed).
    If most neighbors are more exposed than the pocket residue, the pocket
    residue is recessed = concave. If most neighbors are less exposed, it's
    on a convex protrusion = not a pocket.

    Returns fraction of pocket residues in concave positions [0, 1].
    Higher = more geometrically pocket-like.
    """
    coords = np.array([r.ca_coord for r in residues])   # (N, 3)
    centroid = coords.mean(0)
    radii = np.linalg.norm(coords - centroid, axis=1)   # distance from center

    concave_count = 0
    for idx in cluster_residue_idxs:
        r_i = radii[idx]
        # find spatial neighbors within 10A
        dists = np.linalg.norm(coords - coords[idx], axis=1)
        neighbor_idxs = np.where((dists < 10.0) & (dists > 0))[0]
        if len(neighbor_idxs) == 0:
            continue
        neighbor_radii = radii[neighbor_idxs]
        # concave = residue is closer to center than most neighbors
        frac_more_exposed = (neighbor_radii > r_i).mean()
        if frac_more_exposed >= 0.5:
            concave_count += 1

    return concave_count / max(len(cluster_residue_idxs), 1)


# ── Composite confidence score ────────────────────────────────────────────────

def confidence_score(mc_mean: float, mc_std: float,
                     symmetry: float | None,
                     concavity: float) -> float:
    """
    Combine three signals into one confidence value in [0, 1].

    - Uncertainty penalty: high std -> low confidence
    - Symmetry bonus: high chain correlation -> higher confidence
    - Concavity bonus: geometrically recessed -> higher confidence
    """
    uncertainty_conf = float(1.0 - min(mc_std * 4.0, 1.0))  # std=0.25 -> conf=0
    sym_conf = float(symmetry) if symmetry is not None else 0.6  # neutral prior
    geom_conf = concavity

    # weighted combination
    return 0.40 * uncertainty_conf + 0.30 * sym_conf + 0.30 * geom_conf


# ── DBSCAN cluster (recomputed per structure) ─────────────────────────────────

def get_top_cluster_idxs(residues, scores, threshold=THRESHOLD):
    from sklearn.cluster import DBSCAN
    high = np.where(scores >= threshold)[0]
    if len(high) < 3:
        return high
    coords = np.array([residues[i].ca_coord for i in high])
    labels = DBSCAN(eps=6.0, min_samples=3).fit(coords).labels_
    best_label, best_score = -1, -1.0
    for cid in set(labels):
        if cid == -1:
            continue
        idx = high[labels == cid]
        s = scores[idx].mean() * len(idx) ** 0.5
        if s > best_score:
            best_score, best_label = s, cid
    if best_label == -1:
        return high
    return high[labels == best_label]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    model = PocketGNN.small()
    model.load_state_dict(torch.load(CKPT, map_location="cpu", weights_only=True))
    model.eval()

    rows_in = list(csv.DictReader(open(IN_CSV)))
    # Only validate PCNA structures (filter by checking header)
    pcna_pdbs = set()
    for p in RAW_DIR.glob("*.pdb"):
        if "PCNA" in p.read_text(errors="ignore")[:3000].upper() or \
           "PROLIFERATING" in p.read_text(errors="ignore")[:3000].upper():
            pcna_pdbs.add(p.stem)

    pcna_rows = [r for r in rows_in if r["pdb"] in pcna_pdbs]
    print(f"Validating {len(pcna_rows)} PCNA structures with {MC_RUNS} MC-Dropout passes each\n")

    results = []
    flagged = []

    for row in tqdm(pcna_rows, desc="Validating", ncols=90):
        pdb = row["pdb"]
        pdb_path = RAW_DIR / f"{pdb}.pdb"
        if not pdb_path.exists():
            continue
        try:
            residues = parse_pdb(pdb_path)
            data = build_graph_v2(residues)
            n_chains = int(row["n_chains"])

            # 1. MC Dropout
            mc_mean, mc_std = mc_dropout_uncertainty(model, data, MC_RUNS)

            # 2. Symmetry
            sym = trimer_symmetry_score(mc_mean, data.chain_id, n_chains)

            # 3. Geometry
            cluster_idxs = get_top_cluster_idxs(residues, mc_mean)
            geom = concavity_score(residues, cluster_idxs)

            # Top cluster stats using MC mean scores
            top_mean = float(mc_mean[cluster_idxs].mean()) if len(cluster_idxs) else 0.0
            top_std  = float(mc_std[cluster_idxs].mean())  if len(cluster_idxs) else 1.0

            conf = confidence_score(top_mean, top_std, sym, geom)

            # Adjusted score: raw score weighted by confidence
            adjusted = top_mean * conf

            result = {
                "pdb"           : pdb,
                "n_residues"    : row["n_residues"],
                "n_chains"      : row["n_chains"],
                "raw_top_mean"  : round(float(row["top_cluster_mean"]), 4),
                "mc_top_mean"   : round(top_mean, 4),
                "mc_top_std"    : round(top_std,  4),
                "symmetry_corr" : round(sym, 4) if sym is not None else "N/A",
                "concavity"     : round(geom, 4),
                "confidence"    : round(conf, 4),
                "adjusted_score": round(adjusted, 4),
                "gt_hits_top30" : row["gt_hits_top30"],
                "flag"          : "",
            }

            # Flag unreliable predictions
            flags = []
            if top_std > 0.15:
                flags.append("HIGH_UNCERTAINTY")
            if sym is not None and sym < 0.40:
                flags.append("ASYMMETRIC")
            if geom < 0.40:
                flags.append("NOT_CONCAVE")
            result["flag"] = "|".join(flags)
            if flags:
                flagged.append((pdb, flags, round(top_mean, 3), round(conf, 3)))

            results.append(result)

        except Exception as e:
            warnings.warn(f"{pdb}: {e}")

    # ── Save CSV ──────────────────────────────────────────────────────────────
    results.sort(key=lambda r: r["adjusted_score"], reverse=True)
    cols = ["pdb","n_residues","n_chains","raw_top_mean","mc_top_mean","mc_top_std",
            "symmetry_corr","concavity","confidence","adjusted_score","gt_hits_top30","flag"]
    with open(OUT_DIR / "validated_scores.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(results)
    print(f"\n  Saved: {OUT_DIR/'validated_scores.csv'}")

    # ── Save flags ────────────────────────────────────────────────────────────
    with open(OUT_DIR / "flags.txt", "w") as f:
        f.write(f"Flagged structures ({len(flagged)}/{len(results)}):\n\n")
        for pdb, flags, score, conf in sorted(flagged, key=lambda x: -x[2]):
            f.write(f"  {pdb:8s}  score={score:.3f}  conf={conf:.3f}  flags={','.join(flags)}\n")
    print(f"  Saved: {OUT_DIR/'flags.txt'}")

    # ── Print top 20 ─────────────────────────────────────────────────────────
    print(f"\n{'Rank':>4} {'PDB':>6} {'RawMean':>8} {'MCMean':>7} {'Std':>6} "
          f"{'Symm':>6} {'Geom':>6} {'Conf':>6} {'Adj':>6} {'GT':>4}  Flags")
    print("-" * 100)
    for i, r in enumerate(results[:20], 1):
        sym_str = f"{r['symmetry_corr']:6.3f}" if r["symmetry_corr"] != "N/A" else "   N/A"
        flag_str = r["flag"] if r["flag"] else "OK"
        print(f"{i:4d} {r['pdb']:>6} {r['raw_top_mean']:8.4f} {r['mc_top_mean']:7.4f} "
              f"{r['mc_top_std']:6.4f} {sym_str} {r['concavity']:6.3f} "
              f"{r['confidence']:6.3f} {r['adjusted_score']:6.4f} "
              f"{r['gt_hits_top30']:>4}  {flag_str}")

    # ── Confidence plot ───────────────────────────────────────────────────────
    print("\nGenerating confidence plot...")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        raw    = [r["raw_top_mean"]   for r in results]
        adj    = [r["adjusted_score"] for r in results]
        conf   = [r["confidence"]     for r in results]
        pdbs   = [r["pdb"]            for r in results]
        gt     = [int(r["gt_hits_top30"]) for r in results]

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

        # Panel 1: raw vs adjusted score
        ax = axes[0]
        sc = ax.scatter(raw, adj, c=conf, cmap="RdYlGn", vmin=0, vmax=1,
                        s=60, alpha=0.85, edgecolors="none")
        ax.plot([0, 1], [0, 1], "k--", alpha=0.3, linewidth=1)
        ax.set_xlabel("Raw top cluster mean score")
        ax.set_ylabel("Confidence-adjusted score")
        ax.set_title("Raw vs Validated Score\n(color = confidence)")
        plt.colorbar(sc, ax=ax, label="Confidence")
        # label top 5
        top5 = sorted(results, key=lambda r: r["adjusted_score"], reverse=True)[:5]
        for r in top5:
            ax.annotate(r["pdb"], (r["raw_top_mean"], r["adjusted_score"]),
                        fontsize=7, ha="left", va="bottom")

        # Panel 2: confidence components
        ax = axes[1]
        uncertainty_conf = [1.0 - min(r["mc_top_std"] * 4, 1.0) for r in results]
        sym_vals = [float(r["symmetry_corr"]) if r["symmetry_corr"] != "N/A" else 0.6
                    for r in results]
        geom_vals = [r["concavity"] for r in results]
        x = range(len(results))
        ax.bar(x, uncertainty_conf, label="Uncertainty (1-std)", alpha=0.7, color="#3498db")
        ax.bar(x, sym_vals,         label="Symmetry corr",       alpha=0.7, color="#2ecc71",
               bottom=uncertainty_conf)
        ax.set_xticks(range(len(results)))
        ax.set_xticklabels([r["pdb"] for r in results], rotation=90, fontsize=5)
        ax.set_title("Confidence Components per Structure")
        ax.set_ylabel("Component value")
        ax.legend(fontsize=8)

        # Panel 3: GT hits vs adjusted score
        ax = axes[2]
        sc2 = ax.scatter(adj, gt, c=conf, cmap="RdYlGn", vmin=0, vmax=1,
                         s=60, alpha=0.85, edgecolors="none")
        ax.set_xlabel("Confidence-adjusted score")
        ax.set_ylabel("GT pocket hits in top-30 predictions")
        ax.set_title("Adjusted Score vs Ground Truth Recovery\n(color = confidence)")
        plt.colorbar(sc2, ax=ax, label="Confidence")
        for r in top5:
            ax.annotate(r["pdb"], (r["adjusted_score"], int(r["gt_hits_top30"])),
                        fontsize=7, ha="left", va="bottom")

        plt.suptitle("PocketGNN Prediction Validation — PCNA Structures",
                     fontsize=13, fontweight="bold")
        plt.tight_layout()
        fig.savefig(OUT_DIR / "confidence.png", dpi=150)
        plt.close(fig)
        print(f"  Saved: {OUT_DIR/'confidence.png'}")
    except ImportError:
        print("  matplotlib not available")

    # ── Summary stats ─────────────────────────────────────────────────────────
    confs = [r["confidence"] for r in results]
    high_conf = [r for r in results if r["confidence"] >= 0.65 and not r["flag"]]
    print(f"\n=== Validation Summary ===")
    print(f"  Structures validated:        {len(results)}")
    print(f"  Mean confidence score:       {np.mean(confs):.3f}")
    print(f"  High-confidence, clean (>=0.65): {len(high_conf)}")
    print(f"  Flagged as unreliable:       {len(flagged)}")
    print(f"\n  High-confidence predictions worth investigating:")
    for r in high_conf[:10]:
        print(f"    {r['pdb']:8s}  adj={r['adjusted_score']:.4f}  "
              f"conf={r['confidence']:.3f}  GT={r['gt_hits_top30']}")


if __name__ == "__main__":
    main()
