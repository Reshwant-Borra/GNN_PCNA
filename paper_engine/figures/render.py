"""Render publication figures from real Phase-3 data.

Each builder pulls numbers from :mod:`paper_engine.figures.data_loaders` (which
reads real run manifests), draws a journal-grade figure, saves it at 300 DPI to
``paper/figures/``, and returns a :class:`FigureResult` carrying provenance
(source files, the command to regenerate, the reviewer question it answers).

Run directly to render the whole set:
    python -m paper_engine.figures.render
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

import numpy as np

from paper_engine import config
from paper_engine.figures import data_loaders as dl
from paper_engine.figures import style
from paper_engine.figures.figure_specs import FIGURE_SPECS

style.set_style()
import matplotlib.pyplot as plt  # noqa: E402  (after rcParams applied)


# --------------------------------------------------------------------------- #
@dataclass
class FigureResult:
    figure_id: str
    path: str
    title: str
    caption: str
    reviewer_question: str
    claim_support: str
    kind: str
    data_sources: List[str] = field(default_factory=list)
    command: str = ""


def _finalize(fig, figure_id: str, data_sources: List[str]) -> FigureResult:
    config.ensure_output_dirs()
    out_path = config.FIGURES_DIR / f"{figure_id}.png"
    fig.savefig(out_path)
    plt.close(fig)
    spec = FIGURE_SPECS[figure_id]
    # Deduplicate provenance sources, keep order.
    seen: Dict[str, None] = {}
    for s in data_sources:
        seen.setdefault(s, None)
    return FigureResult(
        figure_id=figure_id,
        path=str(out_path),
        title=spec.title,
        caption=spec.caption,
        reviewer_question=spec.reviewer_question,
        claim_support=spec.claim_support,
        kind=spec.kind,
        data_sources=list(seen.keys()),
        command=f"python -m paper_engine.figures.render --only {figure_id}",
    )


def _auprc_axis(ax, hi: float = 0.22) -> None:
    ax.set_xlim(0, hi)
    ax.set_xlabel("Validation macro-AUPRC")
    style.despine(ax)


# --------------------------------------------------------------------------- #
# 1. Baseline comparison
# --------------------------------------------------------------------------- #
def fig_baseline_comparison() -> FigureResult:
    models = [m for m in dl.load_all_models() if m.available]
    # Draw lowest at bottom -> reverse so primary (first) ends on top.
    models = list(reversed(models))
    labels = [m.display for m in models]
    means = [m.mean for m in models]
    errs = [m.sd if m.sd is not None else 0.0 for m in models]
    colors = []
    for m in models:
        if m.kind == "primary":
            colors.append(style.PRIMARY_COLOR)
        elif m.kind == "naive":
            colors.append(style.NAIVE_COLOR)
        elif m.kind == "ablation":
            colors.append(style.ACCENT_COLOR)
        else:
            colors.append(style.BASELINE_COLOR)

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    y = np.arange(len(models))
    ax.barh(y, means, xerr=errs, color=colors, height=0.66,
            error_kw={"elinewidth": 1.0, "capsize": 3, "ecolor": "#444444"})
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    _auprc_axis(ax, hi=max(means) * 1.25)
    for yi, (m, e) in enumerate(zip(means, errs)):
        ax.text(m + e + 0.004, yi, f"{m:.3f}", va="center", ha="left", fontsize=9)
    ax.set_title("Model vs. baselines — validation macro-AUPRC")
    ax.margins(y=0.02)
    fig.text(0.01, -0.02,
             "Same frozen leakage-blocked split · ±1 SD over 4 folds × 3 seeds · test set not evaluated",
             fontsize=8, color="#666666")
    sources = [m.source for m in models]
    return _finalize(fig, "baseline_comparison", sources)


# --------------------------------------------------------------------------- #
# 2. Per-fold performance
# --------------------------------------------------------------------------- #
def fig_per_fold_performance() -> FigureResult:
    wanted = ["graphsage_3l", "gat_2l", "gcn_1l"]
    models = {m.key: m for m in dl.load_all_models()}
    selected = [models[k] for k in wanted if k in models and models[k].per_fold]
    folds = sorted({f for m in selected for f in m.per_fold.keys()})

    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    n = len(selected)
    width = 0.8 / max(n, 1)
    palette = [style.PRIMARY_COLOR, style.BASELINE_COLOR, style.OKABE_ITO["bluish_green"]]
    for i, m in enumerate(selected):
        vals = [m.per_fold.get(f, np.nan) for f in folds]
        x = np.arange(len(folds)) + (i - (n - 1) / 2) * width
        ax.bar(x, vals, width=width, label=m.display, color=palette[i % len(palette)])
    ax.set_xticks(np.arange(len(folds)))
    ax.set_xticklabels([f"Fold {f}" for f in folds])
    ax.set_ylabel("Validation macro-AUPRC")
    ax.set_title("Per-fold validation performance")
    ax.legend(loc="upper left", ncol=len(selected))
    style.despine(ax)
    sources = [m.source for m in selected]
    return _finalize(fig, "per_fold_performance", sources)


# --------------------------------------------------------------------------- #
# 3. Edge-type ablation
# --------------------------------------------------------------------------- #
def fig_ablation_edges() -> FigureResult:
    models = {m.key: m for m in dl.load_all_models()}
    order = [
        ("graphsage_3l", "Full\n(spatial+sequential)"),
        ("sage_no_sequential", "No sequential\nedges"),
        ("sage_no_spatial", "No spatial\nedges"),
    ]
    selected = [(models[k], lab) for k, lab in order if k in models]
    means = [m.mean for m, _ in selected]
    errs = [m.sd if m.sd is not None else 0.0 for m, _ in selected]
    labels = [lab for _, lab in selected]
    colors = [style.PRIMARY_COLOR, style.ACCENT_COLOR, style.NEGATIVE_COLOR]

    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    x = np.arange(len(selected))
    ax.bar(x, means, yerr=errs, color=colors[: len(selected)], width=0.6,
           error_kw={"elinewidth": 1.0, "capsize": 4, "ecolor": "#444444"})
    full_mean = means[0]
    ax.axhline(full_mean, ls="--", lw=1.0, color="#888888", zorder=0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Validation macro-AUPRC")
    ax.set_ylim(0, max(means) * 1.2)
    ax.set_title("Edge-type ablation")
    for xi, (m, e) in enumerate(zip(means, errs)):
        ax.text(xi, m + e + 0.003, f"{m:.3f}", ha="center", va="bottom", fontsize=9)
    style.despine(ax)
    sources = [m.source for m, _ in selected]
    return _finalize(fig, "ablation_edges", sources)


# --------------------------------------------------------------------------- #
# 4. Training curves
# --------------------------------------------------------------------------- #
def fig_training_curves() -> FigureResult:
    primary = dl.load_primary_training()
    fig, ax = plt.subplots(figsize=(7.0, 4.2))

    max_epoch = 0
    curves = []
    for run in primary.runs:
        epochs = [h["epoch"] for h in run.history]
        vals = [h["val_macro_auprc"] for h in run.history]
        if not epochs:
            continue
        max_epoch = max(max_epoch, max(epochs))
        curves.append((epochs, vals))
        ax.plot(epochs, vals, color=style.PRIMARY_COLOR, alpha=0.18, lw=1.0)

    # Across-run mean curve on the common epoch grid.
    if curves:
        grid = np.arange(1, max_epoch + 1)
        stacked = []
        for epochs, vals in curves:
            interp = np.interp(grid, epochs, vals, left=np.nan, right=np.nan)
            stacked.append(interp)
        mean_curve = np.nanmean(np.vstack(stacked), axis=0)
        ax.plot(grid, mean_curve, color=style.ACCENT_COLOR, lw=2.4,
                label="Across-run mean")

    ax.set_xlabel("Epoch")
    ax.set_ylabel("Validation macro-AUPRC")
    ax.set_title("Validation learning curves (12 runs)")
    ax.legend(loc="lower right")
    style.despine(ax)
    return _finalize(fig, "training_curves", [primary.source])


# --------------------------------------------------------------------------- #
# 5. Metric choice (AUPRC vs AUROC)
# --------------------------------------------------------------------------- #
def fig_metric_choice() -> FigureResult:
    models = {m.key: m for m in dl.load_all_models()}
    order = [("graphsage_3l", "GraphSAGE-3L"), ("degree", "Degree"), ("random", "Random")]
    selected = [(models[k], lab) for k, lab in order if k in models]
    labels = [lab for _, lab in selected]
    auprc = [m.mean for m, _ in selected]
    auroc = [m.macro_auroc if m.macro_auroc is not None else np.nan for m, _ in selected]

    label_stats = dl.load_label_stats()
    prevalence = label_stats.get("positive_prevalence") or 0.046

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    x = np.arange(len(selected))
    width = 0.38
    ax.bar(x - width / 2, auprc, width, label="macro-AUPRC", color=style.PRIMARY_COLOR)
    ax.bar(x + width / 2, auroc, width, label="macro-AUROC", color=style.OKABE_ITO["orange"])
    gutter = len(selected) - 0.5 + 0.05
    ax.set_xlim(-0.5, len(selected) - 0.5 + 0.6)
    ax.axhline(prevalence, ls="--", lw=1.0, color=style.PRIMARY_COLOR, alpha=0.7)
    ax.text(gutter, prevalence, f"AUPRC floor\n≈ {prevalence:.3f}",
            ha="left", va="center", fontsize=8, color=style.PRIMARY_COLOR)
    ax.axhline(0.5, ls=":", lw=1.0, color=style.OKABE_ITO["orange"], alpha=0.8)
    ax.text(gutter, 0.5, "AUROC\nchance 0.50", ha="left", va="center",
            fontsize=8, color=style.OKABE_ITO["vermillion"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.0)
    ax.set_title("AUPRC vs AUROC under ~4.6% positive prevalence")
    ax.legend(loc="upper center", ncol=2, bbox_to_anchor=(0.42, 1.0))
    style.despine(ax)
    sources = [m.source for m, _ in selected] + [label_stats["source"]]
    return _finalize(fig, "metric_choice", sources)


# --------------------------------------------------------------------------- #
# 6. Dataset composition + split
# --------------------------------------------------------------------------- #
def fig_dataset_split() -> FigureResult:
    split = dl.load_split_stats()
    labels_stats = dl.load_label_stats()

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(8.4, 3.9),
                                   gridspec_kw={"width_ratios": [1.5, 1.0]})

    # Left: split composition
    dist = split["fold_distribution"]
    train_keys = sorted([k for k in dist if k.startswith("train")])
    ordered = train_keys + (["test"] if "test" in dist else [])
    vals = [dist[k] for k in ordered]
    colors = [style.BASELINE_COLOR] * len(train_keys) + [style.ACCENT_COLOR]
    pretty = [k.replace("train-", "Train fold ").replace("test", "Test (held out)") for k in ordered]
    bars = axl.bar(np.arange(len(ordered)), vals, color=colors[: len(ordered)], width=0.66)
    axl.set_xticks(np.arange(len(ordered)))
    axl.set_xticklabels(pretty, rotation=30, ha="right")
    axl.set_ylabel("Structures")
    axl.set_title("Frozen split (30% identity, PCNA held out)")
    for b, v in zip(bars, vals):
        axl.text(b.get_x() + b.get_width() / 2, v + 2, str(v), ha="center", va="bottom", fontsize=8)
    style.despine(axl)

    # Right: label composition
    pos = labels_stats["total_positives"]
    masked = labels_stats["total_masked"]
    axr.bar([0, 1], [pos, masked],
            color=[style.POSITIVE_COLOR, style.NAIVE_COLOR], width=0.6)
    axr.set_xticks([0, 1])
    axr.set_xticklabels(["Positive\nresidues", "Masked\n(excl. from loss)"])
    axr.set_ylabel("Residues")
    axr.set_title("Label composition")
    for xi, v in zip([0, 1], [pos, masked]):
        axr.text(xi, v + max(pos, masked) * 0.01, f"{v:,}", ha="center", va="bottom", fontsize=8)
    style.despine(axr)

    fig.suptitle(f"Dataset: {labels_stats['structures_labeled']:,} structures · "
                 f"split hash {split['manifest_hash']} · PCNA holdout {split['pcna_holdout_count']}")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return _finalize(fig, "dataset_split", [split["source"], labels_stats["source"]])


# --------------------------------------------------------------------------- #
BUILDERS: Dict[str, Callable[[], FigureResult]] = {
    "baseline_comparison": fig_baseline_comparison,
    "per_fold_performance": fig_per_fold_performance,
    "ablation_edges": fig_ablation_edges,
    "training_curves": fig_training_curves,
    "metric_choice": fig_metric_choice,
    "dataset_split": fig_dataset_split,
}


def render_all(only: Optional[List[str]] = None) -> List[FigureResult]:
    """Render figures (all, or the subset in ``only``) and write the manifest."""
    keys = only or list(BUILDERS.keys())
    results: List[FigureResult] = []
    for key in keys:
        if key not in BUILDERS:
            raise KeyError(f"Unknown figure id: {key}. Known: {list(BUILDERS)}")
        results.append(BUILDERS[key]())
    _write_manifest(results)
    return results


def _write_manifest(results: List[FigureResult]) -> Path:
    config.ensure_output_dirs()
    manifest_path = config.FIGURES_DIR / "figures_manifest.json"
    existing: Dict[str, dict] = {}
    if manifest_path.exists():
        try:
            for item in json.loads(manifest_path.read_text(encoding="utf-8")).get("figures", []):
                existing[item["figure_id"]] = item
        except Exception:
            existing = {}
    for r in results:
        existing[r.figure_id] = asdict(r)
    payload = {
        "schema": "paper_engine.figures/v1",
        "note": "Validation-only figures generated from real Phase-3 run manifests. "
                "Test set not evaluated; no scientific claims.",
        "figures": list(existing.values()),
    }
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return manifest_path


def main() -> None:  # pragma: no cover - CLI entry
    import argparse

    parser = argparse.ArgumentParser(description="Render GNN-PCNA paper figures from real data.")
    parser.add_argument("--only", nargs="*", default=None, help="Subset of figure ids to render.")
    args = parser.parse_args()
    results = render_all(only=args.only)
    print(f"Rendered {len(results)} figure(s) to {config.FIGURES_DIR}")
    for r in results:
        print(f"  [{r.figure_id}] {r.path}")
        print(f"      answers: {r.reviewer_question}")


if __name__ == "__main__":  # pragma: no cover
    main()
