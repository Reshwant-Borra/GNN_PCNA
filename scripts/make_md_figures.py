"""
Generate MD analysis figures for paper Section 3.8.

Reads:
  data/results/md_rmsf_1W60.json
  data/results/md_pocket_volume.json
  data/results/md_dccm_1W60.npy
  data/results/nma_apo_holo_comparison.json  (ANM baseline)

Writes:
  data/results/fig4a_md_rmsf.png        -- per-residue RMSF
  data/results/fig4b_md_pocket_vol.png  -- pocket volume time series
  data/results/fig4c_md_dccm.png        -- DCCM heatmap

Usage:
    python scripts/make_md_figures.py
    python scripts/make_md_figures.py --dpi 300
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import TwoSlopeNorm

REPO    = Path(__file__).parent.parent
RESULTS = REPO / "data" / "results"

AOH_GT = {25,26,27,38,39,40,41,42,44,45,46,47,
          123,125,126,128,231,232,233,234,250,251,252,253}
IDCL   = set(range(119, 134))   # interdomain connecting loop

FONT   = {"family": "sans-serif", "size": 9}
matplotlib.rc("font", **FONT)


# ── helpers ──────────────────────────────────────────────────────────────────

def check(path: Path, label: str) -> bool:
    if not path.exists():
        print(f"  SKIP {label}: {path.name} not found — run run_md_analysis.py first")
        return False
    return True


# ── figure A: per-residue RMSF ───────────────────────────────────────────────

def fig_rmsf(rmsf_json: Path, anm_json: Path, out: Path, dpi: int):
    with open(rmsf_json, encoding="utf-8") as f:
        data = json.load(f)
    with open(anm_json, encoding="utf-8") as f:
        anm  = json.load(f)

    residues = data["residues"]
    resids   = np.array([r["resid"]         for r in residues])
    rmsf     = np.array([r["rmsf_angstrom"] for r in residues])
    in_aoh   = np.array([r["in_aoh_pocket"] for r in residues])

    sim_ns   = round(data.get("sim_time_ns", 0), 1)
    fc_md    = data.get("fold_change_pocket_vs_bg") or \
               (data["pocket_rmsf_angstrom"] / data["background_rmsf_angstrom"]
                if data.get("pocket_rmsf_angstrom") and data.get("background_rmsf_angstrom")
                else None)
    fc_anm   = anm["apo"]["fold_change"]

    fig, ax = plt.subplots(figsize=(7.2, 2.8))

    # background residues
    ax.bar(resids[~in_aoh], rmsf[~in_aoh], width=1.0,
           color="#4878CF", alpha=0.6, label="Background")

    # AOH pocket residues
    ax.bar(resids[in_aoh], rmsf[in_aoh], width=1.2,
           color="#E84646", alpha=0.9, label="AOH1996 pocket")

    # IDCL shading
    idcl_mask = np.array([r in IDCL for r in resids])
    if idcl_mask.any():
        ax.axvspan(resids[idcl_mask].min() - 0.5, resids[idcl_mask].max() + 0.5,
                   color="#F5A623", alpha=0.15, label="IDCL (119–133)")

    # mean lines
    mean_all = rmsf.mean()
    mean_poc = rmsf[in_aoh].mean() if in_aoh.any() else None
    ax.axhline(mean_all, color="black",  lw=0.8, ls="--", label=f"Global mean ({mean_all:.2f} Å)")
    if mean_poc:
        ax.axhline(mean_poc, color="#E84646", lw=0.8, ls=":",
                   label=f"Pocket mean ({mean_poc:.2f} Å)")

    fc_str = f"{fc_md:.3f}" if fc_md else "n/a"
    title  = (f"Apo 1W60 per-residue Cα RMSF  |  {sim_ns} ns MD\n"
              f"Pocket fold-change: MD={fc_str}  ANM={fc_anm:.3f}")
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("Residue ID (per-chain)", fontsize=8)
    ax.set_ylabel("RMSF (Å)", fontsize=8)
    ax.legend(fontsize=7, loc="upper right", framealpha=0.7)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}  (fold-change MD={fc_str}, ANM={fc_anm:.3f})")


# ── figure B: pocket volume time series ──────────────────────────────────────

def fig_pocket_volume(vol_json: Path, out: Path, dpi: int):
    with open(vol_json, encoding="utf-8") as f:
        data = json.load(f)

    frames  = data["frames"]
    times   = np.array([fr["time_ps"] for fr in frames]) / 1000  # → ns
    vols    = np.array([fr["volume_angstrom3"] for fr in frames], dtype=float)
    mean_v  = data["mean_volume_angstrom3"]
    max_v   = data["max_volume_angstrom3"]

    # rolling mean (window = 10% of trajectory)
    win = max(1, len(vols) // 10)
    roll = np.convolve(np.where(np.isnan(vols), 0, vols),
                       np.ones(win)/win, mode="same")

    fig, ax = plt.subplots(figsize=(7.2, 2.5))
    ax.plot(times, vols,  color="#4878CF", lw=0.5, alpha=0.5, label="Per-frame")
    ax.plot(times, roll,  color="#E84646", lw=1.2, label=f"Rolling mean (n={win})")
    ax.axhline(mean_v, color="black",  lw=0.8, ls="--", label=f"Mean {mean_v:.0f} Å³")
    ax.axhline(max_v,  color="#F5A623", lw=0.8, ls=":",  label=f"Max {max_v:.0f} Å³")

    ax.set_title("AOH1996 pocket volume  —  Cα convex hull approximation  |  Apo 1W60", fontsize=9)
    ax.set_xlabel("Time (ns)", fontsize=8)
    ax.set_ylabel("Volume (Å³)", fontsize=8)
    ax.legend(fontsize=7, loc="upper right", framealpha=0.7)
    ax.tick_params(labelsize=7)
    ax.set_xlim(times.min(), times.max())
    fig.tight_layout()
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}  (mean={mean_v:.0f} Å³, max={max_v:.0f} Å³)")


# ── figure C: DCCM heatmap ────────────────────────────────────────────────────

def fig_dccm(dccm_npy: Path, rmsf_json: Path, anm_json: Path, out: Path, dpi: int):
    dccm = np.load(str(dccm_npy))
    with open(rmsf_json, encoding="utf-8") as f:
        rmsf_data = json.load(f)
    with open(anm_json, encoding="utf-8") as f:
        anm = json.load(f)

    residues   = rmsf_data["residues"]
    resids     = np.array([r["resid"] for r in residues])
    in_aoh     = np.array([r["in_aoh_pocket"] for r in residues])
    poc_idx    = np.where(in_aoh)[0]

    # pocket internal DCCM
    if len(poc_idx) >= 2:
        sub = dccm[np.ix_(poc_idx, poc_idx)]
        off = sub[np.triu_indices(len(poc_idx), k=1)]
        poc_dccm_md  = float(off.mean())
    else:
        poc_dccm_md  = float("nan")
    poc_dccm_anm = anm["apo"]["internal_dccm"]

    N = dccm.shape[0]
    fig, ax = plt.subplots(figsize=(5.5, 4.8))
    norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    im   = ax.imshow(dccm, cmap="RdBu_r", norm=norm, origin="upper", aspect="auto")
    plt.colorbar(im, ax=ax, label="DCCM coefficient", shrink=0.8)

    # box around pocket residue block
    if len(poc_idx):
        lo, hi = poc_idx.min() - 0.5, poc_idx.max() + 0.5
        rect   = mpatches.Rectangle((lo, lo), hi-lo, hi-lo,
                                     lw=1.5, edgecolor="#E84646",
                                     facecolor="none", label="AOH1996 pocket")
        ax.add_patch(rect)
        ax.legend(fontsize=7, loc="upper right", framealpha=0.8)

    title = (f"MD DCCM  |  Apo 1W60  |  {N} Cα residues\n"
             f"Pocket internal DCCM: MD={poc_dccm_md:.4f}  ANM={poc_dccm_anm:.4f}")
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("Residue index", fontsize=8)
    ax.set_ylabel("Residue index", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {out.name}  (pocket DCCM: MD={poc_dccm_md:.4f}, ANM={poc_dccm_anm:.4f})")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    rmsf_json = RESULTS / "md_rmsf_1W60.json"
    vol_json  = RESULTS / "md_pocket_volume.json"
    dccm_npy  = RESULTS / "md_dccm_1W60.npy"
    anm_json  = RESULTS / "nma_apo_holo_comparison.json"

    print("Generating MD figures...")

    if check(rmsf_json, "RMSF") and check(anm_json, "ANM"):
        fig_rmsf(rmsf_json, anm_json, RESULTS / "fig4a_md_rmsf.png", args.dpi)

    if check(vol_json, "pocket volume"):
        fig_pocket_volume(vol_json, RESULTS / "fig4b_md_pocket_vol.png", args.dpi)

    if check(dccm_npy, "DCCM") and check(rmsf_json, "RMSF") and check(anm_json, "ANM"):
        fig_dccm(dccm_npy, rmsf_json, anm_json, RESULTS / "fig4c_md_dccm.png", args.dpi)

    print("Done.")


if __name__ == "__main__":
    main()
