"""Figures from the REAL Phase-5 exploratory MD analysis (25 ns, apo 1AXC).

Reads the project's own analysis outputs (RMSD time series, windowed RMSF,
analysis_summary.json) and renders honest figures. The data shows a stable fold
and candidate-pocket residues that are NOT more flexible than the reference
region — i.e. no cryptic-pocket opening on this short timescale. Captions state
this plainly, matching the project's recorded limitations. Nothing is inflated:
the run is 25 ns (one complete replicate + one incomplete), not longer.
"""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from paper_engine import config
from paper_engine.figures import style

style.set_style()
import matplotlib.pyplot as plt  # noqa: E402

_MD_DIR_CANDIDATES = (
    "outputs/phase5_md/time_crunch_1axc_25ns/analysis_fixed",
    "outputs/phase5_md/time_crunch_1axc_25ns",
)


def md_dir() -> Optional[Path]:
    return config.find_data_file(*_MD_DIR_CANDIDATES)


def md_available() -> bool:
    d = md_dir()
    return bool(d and (d / "rmsd_timeseries.csv").exists() and (d / "window_rmsf.csv").exists())


def load_summary() -> dict:
    d = md_dir()
    p = d / "analysis_summary.json" if d else None
    if p and p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def load_rmsd() -> Dict[str, Tuple[List[float], List[float]]]:
    d = md_dir()
    out: Dict[str, Tuple[List[float], List[float]]] = {}
    with open(d / "rmsd_timeseries.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_rep = defaultdict(list)
    for r in rows:
        by_rep[r["replicate"]].append((float(r["time_ns"]), float(r["rmsd_nm"])))
    for rep, pts in by_rep.items():
        pts.sort()
        out[rep] = ([p[0] for p in pts], [p[1] for p in pts])
    return out


def load_rmsf_windows(replicate: str = "replicate_01") -> Dict[str, List[float]]:
    """Per-window RMSF values (nm) for one replicate."""
    d = md_dir()
    by_win = defaultdict(list)
    with open(d / "window_rmsf.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["replicate"] == replicate:
                by_win[r["window"]].append(float(r["rmsf_nm"]))
    return dict(by_win)


def _import_figure_result():
    from paper_engine.figures.render import FigureResult
    return FigureResult


# --------------------------------------------------------------------------- #
def fig_md_rmsd():
    FigureResult = _import_figure_result()
    rmsd = load_rmsd()
    summary = load_summary()
    equil = float(summary.get("equil_ns_discarded", 5.0))

    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    colors = {"replicate_01": style.PRIMARY_COLOR, "replicate_02": style.OKABE_ITO["orange"]}
    for rep, (t, y) in sorted(rmsd.items()):
        reps = summary.get("replicates", {}).get(rep, {})
        incomplete = reps.get("incomplete", False)
        label = f"{rep.replace('_', ' ')}" + (" (incomplete)" if incomplete else "")
        ax.plot(t, y, color=colors.get(rep, style.NAIVE_COLOR), lw=1.4,
                alpha=0.5 if incomplete else 1.0,
                ls="--" if incomplete else "-", label=label)
    ax.axvspan(0, equil, color="#cccccc", alpha=0.35)
    ax.text(equil / 2, ax.get_ylim()[1] * 0.92, f"{equil:.0f} ns\nequilibration\n(discarded)",
            ha="center", va="top", fontsize=8, color="#555555")
    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Backbone RMSD (nm)")
    ax.set_title("Apo 1AXC stability over 25 ns exploratory MD")
    ax.legend(loc="lower right")
    style.despine(ax)

    config.ensure_output_dirs()
    out = config.FIGURES_DIR / "md_rmsd.png"
    fig.savefig(out)
    plt.close(fig)
    rep1 = summary.get("replicates", {}).get("replicate_01", {})
    caption = (
        f"Backbone RMSD versus time for the apo 1AXC simulation (one complete "
        f"replicate to 25 ns; a second replicate is incomplete at 4 ns and shown "
        f"dashed). The first {equil:.0f} ns (shaded) are discarded as equilibration. "
        f"RMSD plateaus near {rep1.get('mean_backbone_rmsd_nm', 0.25):.2f} nm, "
        f"indicating a stable fold over the sampled window. Exploratory only."
    )
    return FigureResult(
        figure_id="md_rmsd", path=str(out), title="Backbone RMSD (25 ns exploratory MD)",
        caption=caption,
        reviewer_question="Did MD actually validate the prediction, or only simulation stability?",
        claim_support="The simulation is stable, so fluctuation analysis reflects "
        "equilibrium dynamics rather than drift.",
        kind="result",
        data_sources=[str(md_dir() / "rmsd_timeseries.csv"), str(md_dir() / "analysis_summary.json")],
        command="python -m paper_engine.figures.md_results")


_WINDOW_ROLE = {
    "239-243": "novel\ncandidate A",
    "28-32": "novel\ncandidate B",
    "206-210": "novel\ncandidate C",
    "134-138": "IDCL-adjacent\ncontrol",
    "118-122": "IDCL/PIP\nreference",
}


def fig_md_rmsf():
    FigureResult = _import_figure_result()
    windows = load_rmsf_windows("replicate_01")

    # Order: reference first, then candidate windows.
    ref_keys = [k for k in windows if "reference" in k]
    cand_keys = sorted(k for k in windows if "reference" not in k)
    order = ref_keys + cand_keys
    means = [statistics.mean(windows[k]) for k in order]
    sds = [statistics.pstdev(windows[k]) if len(windows[k]) > 1 else 0.0 for k in order]
    colors = [style.NAIVE_COLOR] * len(ref_keys) + [style.PRIMARY_COLOR] * len(cand_keys)
    ref_mean = means[0] if ref_keys else 1.0

    def _label(key):
        resrange = key.replace("_reference", "")
        role = _WINDOW_ROLE.get(resrange, "")
        return f"{resrange}\n{role}" if role else resrange

    labels = [_label(k) for k in order]

    fig, ax = plt.subplots(figsize=(7.4, 4.1))
    x = np.arange(len(order))
    ax.bar(x, means, yerr=sds, color=colors, width=0.62,
           error_kw={"elinewidth": 1.0, "capsize": 3, "ecolor": "#444444"})
    if ref_keys:
        ax.axhline(ref_mean, ls="--", lw=1.0, color="#888888", zorder=0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("Backbone RMSF (nm)")
    ax.set_title("Per-window flexibility: candidate residues vs. reference")
    for xi, (m, s) in enumerate(zip(means, sds)):
        ratio = m / ref_mean if ref_mean else 1.0
        tag = f"{m:.3f}\n{ratio:.2f}x" if xi else f"{m:.3f}\n(ref)"
        ax.text(xi, m + s + 0.004, tag, ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, max(m + s for m, s in zip(means, sds)) * 1.28)
    style.despine(ax)

    config.ensure_output_dirs()
    out = config.FIGURES_DIR / "md_rmsf.png"
    fig.savefig(out)
    plt.close(fig)
    caption = (
        "Mean backbone RMSF over the equilibrated 25 ns window for the GNN candidate "
        "pocket residue windows (blue) versus a reference loop region (grey, dashed). "
        "Candidate residues are at or below the reference flexibility — they do NOT "
        "show enhanced mobility, so this short simulation provides no evidence of "
        "cryptic-pocket opening. Consistent with the analysis' own limitation that "
        "RMSD/RMSF alone cannot prove opening; longer timescales and a positive "
        "control are required."
    )
    return FigureResult(
        figure_id="md_rmsf", path=str(out), title="Per-window Cα RMSF (candidate vs reference)",
        caption=caption,
        reviewer_question="Are novel residues experimentally supported?",
        claim_support="Honest negative/inconclusive result: candidate residues are not "
        "more flexible on this timescale, so no opening is claimed.",
        kind="result",
        data_sources=[str(md_dir() / "window_rmsf.csv"), str(md_dir() / "analysis_summary.json")],
        command="python -m paper_engine.figures.md_results")


def render_md_results() -> List:
    """Render the real-MD figures and append them to the figures manifest."""
    if not md_available():
        return []
    from paper_engine.figures.render import _write_manifest

    results = [fig_md_rmsd(), fig_md_rmsf()]
    _write_manifest(results)
    return results


def main() -> None:  # pragma: no cover
    if not md_available():
        print("Real MD analysis not found.")
        return
    results = render_md_results()
    print(f"Rendered {len(results)} real-MD figure(s) to {config.FIGURES_DIR}")
    for r in results:
        print(f"  [{r.figure_id}] {r.path}")


if __name__ == "__main__":  # pragma: no cover
    main()
