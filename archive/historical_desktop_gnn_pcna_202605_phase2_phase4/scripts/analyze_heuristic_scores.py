#!/usr/bin/env python3
"""Heuristic pocket-score analysis (Advay parallel track, Track 5a).

Characterises the `heuristic_pocket_score` field in `friend_crawl_registry.json` and its
source CSV (`data/results/all_structures_scores.csv` inside the local crawl zip).

Key facts established by inspection (recorded so they are not silently assumed):
  - The registry's `heuristic_pocket_score` equals the `mean_score` column of
    all_structures_scores.csv exactly for all four scored structures (1AXC, 1W60, 8GLA,
    1W61). The heuristic is therefore a per-structure mean of per-residue cryptic-pocket
    scores from a prior GNN inference pass (see friend_feature_schema.json).
  - Only 4 of the 72 registry structures carry a non-null score: exactly the 4 CSV rows
    with is_pcna=True. The other 68 are null in the registry.
  - The CSV has 90 rows (4 PCNA + 86 extended-set / non-PCNA structures).

The script writes figures and prints summary stats; the prose interpretation lives in
`reports/phase4/heuristic_score_analysis.md`. It makes NO scientific claim: the heuristic
is a weak prior signal from a non-frozen pipeline and is not the Phase 3 model. It does
not train, evaluate, read the test split, or interpret biology.

Governance: docs/scientific_governance/14_CLAIM_POLICY.md (claim language),
            docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "registries" / "friend_crawl_registry.json"
FIG_DIR = ROOT / "reports" / "phase4" / "figures"
STATS_PATH = ROOT / "reports" / "phase4" / "heuristic_score_stats.json"

ZIP_PATH = Path("C:/Users/advay/GNN_PNCA_crawled_data.zip")
CSV_IN_ZIP = "data/results/all_structures_scores.csv"

POSITIVE_CONTROL_ID = "8GLA"


def load_registry(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_csv_scores() -> list[dict[str, Any]] | None:
    if not ZIP_PATH.exists():
        return None
    with zipfile.ZipFile(ZIP_PATH) as zf:
        if CSV_IN_ZIP not in zf.namelist():
            return None
        text = zf.read(CSV_IN_ZIP).decode("utf-8", "replace")
    return list(csv.DictReader(io.StringIO(text)))


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    records = load_registry(REGISTRY_PATH)

    scored = [r for r in records if r.get("heuristic_pocket_score") is not None]
    null_scored = [r for r in records if r.get("heuristic_pocket_score") is None]
    reg_scores = {r["id"].upper(): r["heuristic_pocket_score"] for r in scored}

    stats: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/analyze_heuristic_scores.py",
        "registry": {
            "n_structures": len(records),
            "n_with_score": len(scored),
            "n_null_score": len(null_scored),
            "scored_structures": reg_scores,
            "null_score_ids": sorted(r["id"] for r in null_scored),
        },
    }

    # --- Figure 1: registry scored structures (n=4) bar chart ---
    fig, ax = plt.subplots(figsize=(6, 4))
    ids = sorted(reg_scores, key=lambda k: reg_scores[k])
    vals = [reg_scores[i] for i in ids]
    colors = ["#c0392b" if i == POSITIVE_CONTROL_ID else "#2c7fb8" for i in ids]
    ax.bar(ids, vals, color=colors)
    ax.set_ylabel("heuristic_pocket_score (mean per-residue)")
    ax.set_title("Registry heuristic scores (only 4/72 are non-null)\nred = 8GLA positive control")
    for i, v in zip(ids, vals):
        ax.text(i, v + 0.002, f"{v:.4f}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "registry_scores_bar.png", dpi=150)
    plt.close(fig)

    # --- Registry scatter: score vs resolution and vs chain_count (n=4) ---
    res = [r["resolution_angstrom"] for r in scored]
    chains = [r["chain_count"] for r in scored]
    sids = [r["id"] for r in scored]
    svals = [r["heuristic_pocket_score"] for r in scored]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, xvals, xlabel in (
        (axes[0], res, "resolution (A)"),
        (axes[1], chains, "chain_count"),
    ):
        ax.scatter(xvals, svals, color="#2c7fb8")
        for x, y, label in zip(xvals, svals, sids):
            ax.annotate(label, (x, y), fontsize=8, xytext=(3, 3), textcoords="offset points")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("heuristic_pocket_score")
    axes[0].set_title("Score vs resolution (registry, n=4)")
    axes[1].set_title("Score vs chain_count (registry, n=4)")
    fig.suptitle("Registry-only scatter: n=4 is too small for correlation claims")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "registry_score_scatter.png", dpi=150)
    plt.close(fig)

    # --- CSV-based broader distribution (context only) ---
    csv_rows = load_csv_scores()
    if csv_rows is not None:
        csv_scores = np.array([float(r["mean_score"]) for r in csv_rows])
        pcna_rows = [r for r in csv_rows if r["is_pcna"].lower() == "true"]
        pcna_scores = np.array([float(r["mean_score"]) for r in pcna_rows])
        gla = reg_scores.get(POSITIVE_CONTROL_ID)
        pct = float((csv_scores < gla).sum()) / len(csv_scores) * 100 if gla else None
        q1, q2, q3 = (float(x) for x in np.percentile(csv_scores, [25, 50, 75]))

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(csv_scores, bins=20, color="#bdbdbd", label=f"all CSV rows (n={len(csv_scores)})")
        for q, name in ((q1, "Q1"), (q2, "median"), (q3, "Q3")):
            ax.axvline(q, color="#636363", linestyle=":", linewidth=1)
            ax.text(q, ax.get_ylim()[1] * 0.9, name, rotation=90, fontsize=7, va="top")
        if gla:
            ax.axvline(gla, color="#c0392b", linestyle="--", linewidth=2,
                       label=f"8GLA={gla:.4f} ({pct:.0f}th pct)")
        ax.scatter(pcna_scores, np.full_like(pcna_scores, 1), color="#2c7fb8",
                   zorder=5, label=f"4 PCNA structures")
        ax.set_xlabel("mean_score (per-residue mean from GNN inference pass)")
        ax.set_ylabel("count")
        ax.set_title("Broader scored set (90 structures: 4 PCNA + 86 extended)\ncontext only -- not the Phase 3 model")
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(FIG_DIR / "csv_score_distribution.png", dpi=150)
        plt.close(fig)

        stats["csv_source"] = {
            "path_in_zip": CSV_IN_ZIP,
            "n_rows": len(csv_rows),
            "n_pcna_rows": len(pcna_rows),
            "min": float(csv_scores.min()),
            "q1": q1,
            "median": q2,
            "q3": q3,
            "max": float(csv_scores.max()),
            "pc_8gla_percentile_in_csv": pct,
            "pc_8gla_in_top_quartile": (gla > q3) if gla else None,
        }
    else:
        stats["csv_source"] = {"status": "SKIPPED_ZIP_OR_CSV_ABSENT"}

    STATS_PATH.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(f"Scored structures (registry): {len(scored)} / {len(records)}")
    print(f"Figures written to {FIG_DIR.relative_to(ROOT)}")
    if csv_rows is not None:
        print(f"8GLA percentile in 90-structure CSV: {stats['csv_source']['pc_8gla_percentile_in_csv']:.1f}")
    print(f"Stats written to {STATS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
