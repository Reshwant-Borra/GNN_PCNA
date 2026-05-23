"""Regenerate PCNA reports with the clean-split xl_esm_full checkpoint only.

Outputs are labeled as:
ESM2-augmented GNN prioritization results.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.cluster import DBSCAN
from sklearn.metrics import roc_auc_score

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.data_processing.graph_construction import build_graph_v2
from src.data_processing.parse_pdb import (
    get_ligand_coords,
    label_pocket_residues,
    parse_pdb,
)
from src.models import PocketGNNXL

RAW = REPO / "data" / "raw"
ESM_DIR = REPO / "data" / "esm_features"
OUT = REPO / "results" / "per_structure"
FIG_DIR = REPO / "results" / "figures"
RESULT_LABEL = "ESM2-augmented GNN prioritization results."
DEFAULT_CKPT = REPO / "checkpoints" / "clean_split" / "xl_esm_full" / "seed_42" / "best.ckpt"
DEFAULT_EVAL = REPO / "data" / "results" / "clean_split_evaluation.json"

PCNA_CHAIN_WHITELIST: dict[str, set[str]] = {
    "1AXC": {"A", "C", "E"},
    "9B8T": {"B", "C", "D"},
}

AOH_GT_BY_CHAIN: dict[str, set[int]] = {
    "A": {25, 26, 27, 38, 39, 40, 41, 42, 44, 45, 46, 47,
          123, 125, 126, 128, 231, 232, 233, 234, 250, 251, 252, 253},
    "B": {23, 25, 26, 27, 38, 39, 40, 41, 42, 44, 45, 46, 47,
          123, 125, 126, 128, 231, 232, 233, 234, 250, 251, 252},
}
AOH_GT_FLAT = set().union(*AOH_GT_BY_CHAIN.values())

PCNA_REGIONS = [
    (1, 40, "N-terminal beta sheet (domain 1)"),
    (38, 47, "Front-face loop (PIP-box groove)"),
    (119, 134, "IDCL - Interdomain Connecting Loop"),
    (135, 230, "Domain 2 core beta sheet"),
    (231, 253, "C-terminal loop - AOH1996 cryptic pocket region"),
    (250, 261, "C-terminal tail (protein-protein interface)"),
]

SKIP_LIGANDS = {
    "HOH", "WAT", "SO4", "EDO", "PEG", "GOL", "DMS", "PO4", "MPD",
    "FMT", "ACT", "MES", "HED", "BME", "DTT", "EPE", "NHE", "IMD",
    "CIT", "TRS", "FLC", "SCN", "AZI", "NO3", "PGE", "PE5", "PE7",
    "NH4", "ACE", "MSE", "SEP", "TPO", "PTR", "MG", "CA", "ZN",
    "MN", "FE", "CU", "NA", "K", "CD", "AU", "PT", "CO", "NI",
    "HG", "SE", "BR", "CL", "IOD", "AGS", "ADP", "ATP", "GTP",
    "GDP", "TTP", "TMP", "DTP", "SF4", "FES", "F3S", "DOC", "APC",
    "ANP", "AMP", "CTP", "UTP", "NAD", "FAD", "FMN",
}


def region_label(resid: int) -> str:
    """Map PCNA residue number to a coarse structural region."""
    for lo, hi, name in PCNA_REGIONS:
        if lo <= resid <= hi:
            return name
    return "Core beta sheet"


def get_title(pdb_path: Path) -> str:
    """Extract a short PDB title/header."""
    title = ""
    for line in pdb_path.read_text(errors="ignore").splitlines()[:40]:
        if line.startswith("TITLE"):
            title += line[10:].strip() + " "
        elif line.startswith("HEADER") and not title:
            title = line[10:50].strip()
    return title.strip()[:140]


def find_pcna_pdbs() -> list[Path]:
    """Find raw PDB files that are PCNA structures."""
    out = []
    for path in sorted(RAW.glob("*.pdb")):
        text = path.read_text(errors="ignore")[:4000].upper()
        if "PCNA" in text or "PROLIFERATING CELL NUCLEAR ANTIGEN" in text:
            out.append(path)
    return out


def find_ligands(pdb_path: Path) -> list[str]:
    """Return non-solvent/non-cofactor HETATM residue names."""
    found: list[str] = []
    seen = set()
    for line in pdb_path.read_text(errors="ignore").splitlines():
        if line.startswith("HETATM"):
            name = line[17:20].strip()
            if name and name not in SKIP_LIGANDS and name not in seen:
                seen.add(name)
                found.append(name)
    return found


def auto_labels(pdb_path: Path, residues) -> np.ndarray | None:
    """Create ligand-proximity labels for local sanity summaries only."""
    coords = []
    for ligand in find_ligands(pdb_path):
        ligand_coords = get_ligand_coords(pdb_path, resname=ligand)
        if ligand_coords is not None:
            coords.append(ligand_coords)
    if not coords:
        return None
    return label_pocket_residues(residues, np.vstack(coords), cutoff_angstrom=6.0)


def load_threshold(eval_path: Path, condition: str, seed: int, fallback: float) -> float:
    """Load the validation-selected threshold from clean-split evaluation JSON."""
    if not eval_path.exists():
        return fallback
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    for run in data.get("runs_by_condition", {}).get(condition, []):
        if int(run.get("seed", -1)) == seed:
            return float(run["validation_selected_threshold"])
    return fallback


def load_model(ckpt: Path) -> PocketGNNXL:
    """Load a 520-dim PocketGNNXL checkpoint."""
    state = torch.load(str(ckpt), map_location="cpu", weights_only=True)
    node_dim = state["node_encoder.0.weight"].shape[1]
    if node_dim != 520:
        raise ValueError(f"{ckpt} has node_dim={node_dim}; expected 520 for xl_esm_full")
    model = PocketGNNXL(node_in_dim=520).eval()
    model.load_state_dict(state)
    return model


def filtered_residues_and_esm(pdb: str, pdb_path: Path):
    """Parse residues, apply PCNA chain filter, and align ESM rows."""
    residues_all = parse_pdb(pdb_path)
    esm_path = ESM_DIR / f"{pdb}.npy"
    if not esm_path.exists():
        raise FileNotFoundError(f"Missing ESM2 features: {esm_path}")
    esm_all = np.load(esm_path)
    if len(residues_all) != int(esm_all.shape[0]):
        raise ValueError(f"{pdb}: ESM rows {esm_all.shape[0]} != parsed residues {len(residues_all)}")

    keep_chains = PCNA_CHAIN_WHITELIST.get(pdb)
    if keep_chains is None:
        keep = np.ones(len(residues_all), dtype=bool)
    else:
        keep = np.array([r.chain in keep_chains for r in residues_all], dtype=bool)
    residues = [r for r, ok in zip(residues_all, keep) if ok]
    esm = torch.from_numpy(esm_all[keep]).float()
    return residues, esm, sorted(set(r.chain for r in residues))


def aoh_overlap(residues, idxs: list[int]) -> int:
    """Count chain-aware AOH1996 residue overlap in a predicted cluster."""
    hits = 0
    for i in idxs:
        r = residues[i]
        if r.resid in AOH_GT_BY_CHAIN.get(r.chain, set()):
            hits += 1
    return hits


def concavity(residues, idxs: list[int]) -> float:
    """Estimate whether cluster residues sit in a concave neighborhood."""
    if not idxs:
        return 0.0
    coords = np.array([r.ca_coord for r in residues])
    centroid = coords.mean(axis=0)
    radii = np.linalg.norm(coords - centroid, axis=1)
    concave = 0
    for i in idxs:
        dists = np.linalg.norm(coords - coords[i], axis=1)
        nbrs = np.where((dists < 10.0) & (dists > 0.0))[0]
        if len(nbrs) and float((radii[nbrs] > radii[i]).mean()) >= 0.5:
            concave += 1
    return concave / len(idxs)


def cluster_pockets(residues, scores: np.ndarray, threshold: float) -> list[dict]:
    """Cluster high-scoring residues into candidate pockets."""
    high = np.where(scores >= threshold)[0]
    if len(high) < 3:
        return []
    coords = np.array([residues[i].ca_coord for i in high])
    labels = DBSCAN(eps=6.0, min_samples=3).fit(coords).labels_
    clusters = []
    for label in sorted(set(labels)):
        if label < 0:
            continue
        idx = high[labels == label]
        cluster_scores = scores[idx]
        center = np.array([residues[i].ca_coord for i in idx]).mean(axis=0)
        clusters.append({
            "rank": 0,
            "n_residues": int(len(idx)),
            "mean_score": float(cluster_scores.mean()),
            "max_score": float(cluster_scores.max()),
            "center_x": float(center[0]),
            "center_y": float(center[1]),
            "center_z": float(center[2]),
            "residue_idxs": [int(i) for i in idx],
            "aoh_overlap": 0,
            "concavity": 0.0,
        })
    clusters.sort(key=lambda c: c["mean_score"] * np.sqrt(c["n_residues"]), reverse=True)
    for rank, cluster in enumerate(clusters, start=1):
        cluster["rank"] = rank
        cluster["aoh_overlap"] = aoh_overlap(residues, cluster["residue_idxs"])
        cluster["concavity"] = concavity(residues, cluster["residue_idxs"])
    return clusters


def write_scores(out_dir: Path, residues, scores: np.ndarray, labels: np.ndarray | None,
                 threshold: float) -> None:
    """Write per-residue score table."""
    with (out_dir / "scores.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "result_label", "chain", "resid", "resname", "score", "above_threshold",
            "threshold", "region", "gt_aoh", "auto_ligand_label",
        ])
        for i, (residue, score) in enumerate(zip(residues, scores)):
            gt_aoh = int(residue.resid in AOH_GT_BY_CHAIN.get(residue.chain, set()))
            auto_label = "" if labels is None else int(labels[i])
            writer.writerow([
                RESULT_LABEL, residue.chain, residue.resid, residue.resname,
                f"{float(score):.6f}", int(float(score) >= threshold), f"{threshold:.6f}",
                region_label(residue.resid), gt_aoh, auto_label,
            ])


def write_clusters(out_dir: Path, residues, scores: np.ndarray, clusters: list[dict]) -> None:
    """Write cluster summary table."""
    with (out_dir / "clusters.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "result_label", "rank", "n_residues", "mean_score", "max_score",
            "center_x", "center_y", "center_z", "aoh_overlap", "concavity",
            "dominant_region", "residues",
        ])
        for cluster in clusters:
            idxs = cluster["residue_idxs"]
            region_counts: dict[str, int] = {}
            residue_labels = []
            for i in idxs:
                residue = residues[i]
                region = region_label(residue.resid)
                region_counts[region] = region_counts.get(region, 0) + 1
                residue_labels.append(
                    f"{residue.chain}{residue.resid}({residue.resname})={scores[i]:.4f}"
                )
            dominant = max(region_counts, key=region_counts.get) if region_counts else ""
            writer.writerow([
                RESULT_LABEL, cluster["rank"], cluster["n_residues"],
                f"{cluster['mean_score']:.6f}", f"{cluster['max_score']:.6f}",
                f"{cluster['center_x']:.3f}", f"{cluster['center_y']:.3f}",
                f"{cluster['center_z']:.3f}", cluster["aoh_overlap"],
                f"{cluster['concavity']:.3f}", dominant, ";".join(residue_labels),
            ])


def write_report(out_dir: Path, pdb: str, title: str, chains: list[str], residues,
                 scores: np.ndarray, clusters: list[dict], ligands: list[str],
                 labels: np.ndarray | None, auroc: float | None, threshold: float,
                 ckpt: Path) -> None:
    """Write a concise human-readable report."""
    lines = [
        "=" * 72,
        f"PDB: {pdb}",
        f"Result label: {RESULT_LABEL}",
        f"Checkpoint: {ckpt.relative_to(REPO)}",
        f"Title: {title}",
        f"Chains analyzed: {', '.join(chains)} | Residues: {len(residues)}",
        f"Threshold: {threshold:.6f} (clean-split validation-selected threshold)",
        f"Ligands detected: {', '.join(ligands) if ligands else 'none'}",
        "Benchmark note: no random-split or contaminated benchmark metrics are used here.",
        "Interpretation note: these are prioritization scores, not validated pockets.",
    ]
    if auroc is not None:
        lines.append(f"Auto-ligand AUROC sanity summary: {auroc:.4f} (not a benchmark claim)")
    lines.extend([
        f"Score max/mean/std: {scores.max():.4f} / {scores.mean():.4f} / {scores.std():.4f}",
        f"Residues above threshold: {int((scores >= threshold).sum())}/{len(scores)}",
        "",
    ])
    if not clusters:
        lines.append("No DBSCAN clusters met the threshold.")
    else:
        lines.append(f"Predicted candidate clusters: {len(clusters)}")
        for cluster in clusters[:10]:
            idxs = cluster["residue_idxs"]
            top = sorted(idxs, key=lambda i: scores[i], reverse=True)[:10]
            region_counts: dict[str, int] = {}
            for i in idxs:
                region = region_label(residues[i].resid)
                region_counts[region] = region_counts.get(region, 0) + 1
            dominant = max(region_counts, key=region_counts.get) if region_counts else ""
            top_text = ", ".join(
                f"{residues[i].chain}{residues[i].resid}({residues[i].resname})={scores[i]:.3f}"
                for i in top
            )
            lines.extend([
                "",
                f"Pocket #{cluster['rank']}",
                f"  Residues: {cluster['n_residues']} | Mean: {cluster['mean_score']:.4f} | Max: {cluster['max_score']:.4f}",
                f"  Center: ({cluster['center_x']:.1f}, {cluster['center_y']:.1f}, {cluster['center_z']:.1f})",
                f"  Dominant region: {dominant}",
                f"  AOH1996 overlap: {cluster['aoh_overlap']} residues",
                f"  Concavity: {cluster['concavity']:.3f}",
                f"  Top residues: {top_text}",
            ])
    (out_dir / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_rankings(rows: list[dict]) -> None:
    """Write ranking bar plot and score/AOH scatter."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    ranked = sorted(rows, key=lambda row: row["top_cluster_mean"], reverse=True)
    labels = [row["pdb"] for row in ranked]
    values = [row["top_cluster_mean"] for row in ranked]
    colors = [
        "#d95f02" if row["pdb"] in {"8GLA", "8GL9", "8GCJ"}
        else "#1b9e77" if row["pdb"] in {"1W60", "4RJF", "1U7B"}
        else "#7570b3"
        for row in ranked
    ]

    fig, ax = plt.subplots(figsize=(22, 7))
    ax.bar(range(len(ranked)), values, color=colors, width=0.82)
    ax.set_xticks(range(len(ranked)))
    ax.set_xticklabels(labels, rotation=90, fontsize=6)
    ax.set_ylabel("Top cluster mean score")
    ax.set_title(RESULT_LABEL)
    ax.set_ylim(0, max(values + [1.0]) * 1.05)
    fig.tight_layout()
    fig.savefig(OUT / "ranked.png", dpi=160)
    fig.savefig(FIG_DIR / "pcna_xl_esm_full_ranked.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(
        [row["top_cluster_mean"] for row in rows],
        [row["top_aoh_overlap"] for row in rows],
        c=colors,
        alpha=0.85,
    )
    for row in rows:
        if row["top_aoh_overlap"] >= 10 or row["pdb"] in {"8GLA", "1W60", "9B8T"}:
            ax.annotate(row["pdb"], (row["top_cluster_mean"], row["top_aoh_overlap"]), fontsize=7)
    ax.set_xlabel("Top cluster mean score")
    ax.set_ylabel("AOH1996 overlap in top cluster")
    ax.set_title(RESULT_LABEL)
    fig.tight_layout()
    fig.savefig(OUT / "score_vs_aoh_overlap.png", dpi=160)
    fig.savefig(FIG_DIR / "pcna_xl_esm_full_score_vs_aoh.png", dpi=160)
    plt.close(fig)


def plot_profiles(rows: list[dict], top_n: int = 20) -> None:
    """Write score profiles for the top-ranked structures."""
    top = sorted(rows, key=lambda row: row["top_cluster_mean"], reverse=True)[:top_n]
    ncols = 4
    nrows = int(np.ceil(len(top) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(22, 3.5 * nrows))
    axes = np.array(axes).reshape(-1)
    for ax, row in zip(axes, top):
        score_path = OUT / row["pdb"] / "scores.csv"
        per_residue = list(csv.DictReader(score_path.open(encoding="utf-8")))
        chains = list(dict.fromkeys(item["chain"] for item in per_residue))
        for chain in chains:
            chain_rows = [item for item in per_residue if item["chain"] == chain]
            ax.plot(
                [int(item["resid"]) for item in chain_rows],
                [float(item["score"]) for item in chain_rows],
                linewidth=0.9,
                label=f"Chain {chain}",
            )
        for resid in AOH_GT_FLAT:
            ax.axvspan(resid - 0.5, resid + 0.5, color="#d95f02", alpha=0.06)
        ax.set_ylim(0.0, 1.02)
        ax.set_title(f"{row['pdb']} top={row['top_cluster_mean']:.3f}", fontsize=8)
        ax.tick_params(labelsize=6)
    for ax in axes[len(top):]:
        ax.set_visible(False)
    fig.suptitle(RESULT_LABEL, fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "profiles.png", dpi=150)
    fig.savefig(FIG_DIR / "pcna_xl_esm_full_profiles.png", dpi=150)
    plt.close(fig)


def plot_full_analysis(rows: list[dict]) -> None:
    """Write the canonical per-structure full analysis figure."""
    ranked = sorted(rows, key=lambda row: row["top_cluster_mean"], reverse=True)
    labels = [row["pdb"] for row in ranked]
    top_means = [row["top_cluster_mean"] for row in ranked]
    aoh = [row["top_aoh_overlap"] for row in ranked]
    n_above = [row["n_above_threshold"] for row in ranked]

    fig = plt.figure(figsize=(24, 16))
    fig.suptitle(RESULT_LABEL, fontsize=16, fontweight="bold")

    ax1 = fig.add_subplot(3, 1, 1)
    colors = [
        "#d95f02" if row["pdb"] in {"8GLA", "8GL9", "8GCJ"}
        else "#1b9e77" if row["pdb"] in {"1W60", "4RJF", "1U7B"}
        else "#7570b3"
        for row in ranked
    ]
    ax1.bar(range(len(ranked)), top_means, color=colors, width=0.82)
    ax1.set_xticks(range(len(ranked)))
    ax1.set_xticklabels(labels, rotation=90, fontsize=6)
    ax1.set_ylabel("Top cluster mean score")
    ax1.set_title("PCNA ranking by clean-split xl_esm_full checkpoint")

    ax2 = fig.add_subplot(3, 2, 3)
    ax2.scatter(top_means, aoh, c=colors, alpha=0.85)
    for row in ranked:
        if row["top_aoh_overlap"] >= 3 or row["pdb"] in {"8GLA", "1W60", "8GL9"}:
            ax2.annotate(row["pdb"], (row["top_cluster_mean"], row["top_aoh_overlap"]), fontsize=7)
    ax2.set_xlabel("Top cluster mean score")
    ax2.set_ylabel("AOH1996 overlap")
    ax2.set_title("Top cluster score vs AOH-region overlap")

    ax3 = fig.add_subplot(3, 2, 4)
    ax3.hist([row["score_mean"] for row in rows], bins=20, color="#7570b3", edgecolor="white")
    ax3.set_xlabel("Mean residue score")
    ax3.set_ylabel("Structures")
    ax3.set_title("Distribution of mean residue scores")

    ax4 = fig.add_subplot(3, 2, 5)
    ax4.scatter(top_means, n_above, c=colors, alpha=0.85)
    ax4.set_xlabel("Top cluster mean score")
    ax4.set_ylabel("Residues above threshold")
    ax4.set_title("Signal size at validation-selected threshold")

    ax5 = fig.add_subplot(3, 2, 6)
    sanity = [float(row["auto_ligand_auroc_sanity"]) for row in rows if row["auto_ligand_auroc_sanity"]]
    if sanity:
        ax5.hist(sanity, bins=10, color="#1b9e77", edgecolor="white")
    ax5.set_xlabel("Auto-ligand AUROC sanity summary")
    ax5.set_ylabel("Structures")
    ax5.set_title("Ligand-proximity sanity summaries only, not benchmark metrics")

    fig.tight_layout(rect=(0, 0, 1, 0.965))
    fig.savefig(OUT / "full_analysis.png", dpi=150)
    fig.savefig(FIG_DIR / "pcna_xl_esm_full_full_analysis.png", dpi=150)
    plt.close(fig)


def write_global_tables(rows: list[dict]) -> None:
    """Write global rankings and pocket score summaries."""
    OUT.mkdir(parents=True, exist_ok=True)
    cols = [
        "result_label", "pdb", "title", "n_residues", "n_chains", "chains",
        "ligands", "auto_ligand_auroc_sanity", "n_clusters", "top_cluster_mean",
        "top_cluster_max", "top_cluster_n", "top_aoh_overlap", "top_concavity",
        "score_max", "score_mean", "score_std", "n_above_threshold", "threshold",
        "checkpoint",
    ]
    ranked = sorted(rows, key=lambda row: row["top_cluster_mean"], reverse=True)
    for filename in ("summary_table.csv", "pcna_rankings.csv", "pocket_score_summaries.csv"):
        with (OUT / filename).open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(ranked)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ckpt", type=Path, default=DEFAULT_CKPT)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--eval-json", type=Path, default=DEFAULT_EVAL)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    threshold = args.threshold
    if threshold is None:
        threshold = load_threshold(args.eval_json, "xl_esm_full", args.seed, fallback=0.700110)

    model = load_model(args.ckpt)
    checkpoint_label = str(args.ckpt.relative_to(REPO))
    pdb_paths = find_pcna_pdbs()
    print(f"{RESULT_LABEL}")
    print(f"Checkpoint: {checkpoint_label}")
    print(f"Threshold: {threshold:.6f}")
    print(f"PCNA structures: {len(pdb_paths)}")

    rows = []
    generated = []
    for pdb_path in pdb_paths:
        pdb = pdb_path.stem.upper()
        residues, esm, chains = filtered_residues_and_esm(pdb, pdb_path)
        graph = build_graph_v2(residues)
        if graph.x.shape[0] != esm.shape[0]:
            raise ValueError(f"{pdb}: graph nodes {graph.x.shape[0]} != ESM rows {esm.shape[0]}")
        x = torch.cat([graph.x, esm], dim=1)
        with torch.no_grad():
            scores = model(
                x, graph.edge_index, graph.edge_attr,
                graph.edge_index_seq, graph.edge_attr_seq, graph.chain_id,
            ).cpu().numpy()

        ligands = find_ligands(pdb_path)
        labels = auto_labels(pdb_path, residues)
        auroc = None
        if labels is not None and labels.sum() >= 2 and (1 - labels).sum() >= 2:
            auroc = float(roc_auc_score(labels, scores))

        clusters = cluster_pockets(residues, scores, threshold)
        top = clusters[0] if clusters else {}
        out_dir = OUT / pdb
        out_dir.mkdir(parents=True, exist_ok=True)
        write_scores(out_dir, residues, scores, labels, threshold)
        write_clusters(out_dir, residues, scores, clusters)
        write_report(
            out_dir, pdb, get_title(pdb_path), chains, residues, scores, clusters,
            ligands, labels, auroc, threshold, args.ckpt,
        )
        summary = {
            "result_label": RESULT_LABEL,
            "pdb": pdb,
            "title": get_title(pdb_path),
            "n_residues": len(residues),
            "n_chains": len(chains),
            "chains": ",".join(chains),
            "ligands": "|".join(ligands),
            "auto_ligand_auroc_sanity": "" if auroc is None else f"{auroc:.6f}",
            "n_clusters": len(clusters),
            "top_cluster_mean": float(top.get("mean_score", 0.0)),
            "top_cluster_max": float(top.get("max_score", 0.0)),
            "top_cluster_n": int(top.get("n_residues", 0)),
            "top_aoh_overlap": int(top.get("aoh_overlap", 0)),
            "top_concavity": float(top.get("concavity", 0.0)),
            "score_max": float(scores.max()),
            "score_mean": float(scores.mean()),
            "score_std": float(scores.std()),
            "n_above_threshold": int((scores >= threshold).sum()),
            "threshold": float(threshold),
            "checkpoint": checkpoint_label,
        }
        (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        rows.append(summary)
        generated.extend([
            out_dir / "scores.csv", out_dir / "clusters.csv",
            out_dir / "report.txt", out_dir / "summary.json",
        ])
        print(
            f"{pdb:6s} top={summary['top_cluster_mean']:.4f} "
            f"n={summary['top_cluster_n']:3d} clusters={len(clusters):2d} "
            f"aoh={summary['top_aoh_overlap']:2d}"
        )

    write_global_tables(rows)
    plot_rankings(rows)
    plot_profiles(rows)
    plot_full_analysis(rows)
    generated.extend([
        OUT / "summary_table.csv",
        OUT / "pcna_rankings.csv",
        OUT / "pocket_score_summaries.csv",
        OUT / "ranked.png",
        OUT / "score_vs_aoh_overlap.png",
        OUT / "profiles.png",
        OUT / "full_analysis.png",
        FIG_DIR / "pcna_xl_esm_full_ranked.png",
        FIG_DIR / "pcna_xl_esm_full_score_vs_aoh.png",
        FIG_DIR / "pcna_xl_esm_full_profiles.png",
        FIG_DIR / "pcna_xl_esm_full_full_analysis.png",
    ])
    manifest = {
        "result_label": RESULT_LABEL,
        "checkpoint": checkpoint_label,
        "threshold": threshold,
        "n_structures": len(rows),
        "generated_files": [str(path.relative_to(REPO)) for path in generated],
    }
    (OUT / "regeneration_manifest_xl_esm_full.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Generated manifest: {OUT / 'regeneration_manifest_xl_esm_full.json'}")


if __name__ == "__main__":
    main()
