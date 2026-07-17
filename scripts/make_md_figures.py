"""
Generate MD analysis figures for paper Section 3.8 (CORRECTED, per-chain).

Reads (produced by run_md_analysis.py):
  data/results/md_pocket_volume.json   -- per-chain volume/SASA/mouth series
  data/results/md_rmsf.json            -- per-residue, per-chain RMSF
  data/results/md_dccm.npy             -- chain-averaged Cα DCCM
  data/results/nma_apo_holo_comparison.json  -- ANM baseline (optional)

Writes:
  data/results/fig4a_md_rmsf.png        -- per-residue RMSF (chain-averaged)
  data/results/fig4b_md_pocket_vol.png  -- per-chain pocket volume time series
  data/results/fig4c_md_dccm.png        -- DCCM heatmap

Usage:
    python scripts/make_md_figures.py
    python scripts/make_md_figures.py --dpi 300
"""
from __future__ import annotations
import argparse, json
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import TwoSlopeNorm

REPO    = Path(__file__).parent.parent
RESULTS = REPO / "data" / "results"

AOH_RESSEQ = {25, 26, 27, 38, 39, 40, 41, 42, 44, 45, 46, 47,
              123, 125, 126, 128, 231, 232, 233, 234, 250, 251, 252, 253}
IDCL   = set(range(119, 134))   # interdomain connecting loop
CHAIN_COLORS = ["#4878CF", "#E84646", "#59A14F"]

matplotlib.rc("font", **{"family": "sans-serif", "size": 9})


def check(path: Path, label: str) -> bool:
    if not path.exists():
        print(f"  SKIP {label}: {path.name} not found — run run_md_analysis.py first")
        return False
    return True


# ── figure A: per-residue RMSF, averaged across the 3 homotrimer chains ───────

def fig_rmsf(rmsf_json: Path, anm_json: Path | None, out: Path, dpi: int):
    data = json.loads(rmsf_json.read_text(encoding="utf-8"))
    residues = data["residues"]
    # average RMSF per resid across chains (homotrimer symmetry) — avoids the old
    # bug where 3 chains collided onto the same x positions.
    by_resid_pocket = defaultdict(list)
    by_resid_flag = {}
    for r in residues:
        by_resid_pocket[int(r["resid"])].append(float(r["rmsf_angstrom"]))
        by_resid_flag[int(r["resid"])] = by_resid_flag.get(int(r["resid"]), False) or bool(r["in_aoh_pocket"])
    resids = np.array(sorted(by_resid_pocket))
    rmsf = np.array([np.mean(by_resid_pocket[r]) for r in resids])
    in_aoh = np.array([by_resid_flag[r] for r in resids])

    struct = data.get("structure", "apo")
    fc_md = data.get("fold_change_pocket_vs_bg")
    fc_anm = None
    if anm_json and anm_json.exists():
        try:
            fc_anm = json.loads(anm_json.read_text(encoding="utf-8"))["apo"]["fold_change"]
        except Exception:
            fc_anm = None

    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.bar(resids[~in_aoh], rmsf[~in_aoh], width=1.0, color="#4878CF", alpha=0.6, label="Background")
    ax.bar(resids[in_aoh], rmsf[in_aoh], width=1.6, color="#E84646", alpha=0.95, label="AOH1996 pocket")
    idcl_mask = np.array([r in IDCL for r in resids])
    if idcl_mask.any():
        ax.axvspan(resids[idcl_mask].min() - 0.5, resids[idcl_mask].max() + 0.5,
                   color="#F5A623", alpha=0.15, label="IDCL (119–133)")
    ax.axhline(rmsf.mean(), color="black", lw=0.8, ls="--", label=f"Global mean ({rmsf.mean():.2f} Å)")
    if in_aoh.any():
        ax.axhline(rmsf[in_aoh].mean(), color="#E84646", lw=0.8, ls=":",
                   label=f"Pocket mean ({rmsf[in_aoh].mean():.2f} Å)")

    fc_str = f"{fc_md:.3f}" if isinstance(fc_md, (int, float)) else "n/a"
    anm_str = f"  ANM={fc_anm:.3f}" if isinstance(fc_anm, (int, float)) else ""
    ax.set_title(f"{struct} per-residue Cα RMSF (chain-averaged)\n"
                 f"Pocket vs background fold-change: MD={fc_str}{anm_str}", fontsize=9)
    ax.set_xlabel("Residue ID (per-chain)", fontsize=8)
    ax.set_ylabel("RMSF (Å)", fontsize=8)
    ax.legend(fontsize=7, loc="upper right", framealpha=0.7)
    ax.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(out, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    print(f"  Saved {out.name}  (MD fold-change={fc_str})")


# ── figure B: per-chain pocket volume time series (the pocket breathing) ──────

def fig_pocket_volume(vol_json: Path, out: Path, dpi: int):
    data = json.loads(vol_json.read_text(encoding="utf-8"))
    chains = data["chains"]
    agg = data.get("aggregate", {})
    struct = data.get("structure", "apo")

    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    for i, (ch, cd) in enumerate(sorted(chains.items())):
        t = np.array(cd["times_ns"], dtype=float)
        v = np.array(cd["volume_A3"], dtype=float)
        color = CHAIN_COLORS[i % len(CHAIN_COLORS)]
        ax.plot(t, v, lw=0.8, alpha=0.85, color=color, label=f"chain {ch}")
        # per-chain rolling mean, NaN-safe
        good = ~np.isnan(v)
        if good.sum() > 10:
            win = max(1, good.sum() // 10)
            vv = np.interp(np.arange(len(v)), np.where(good)[0], v[good])
            roll = np.convolve(vv, np.ones(win) / win, mode="valid")
            ax.plot(t[win - 1:], roll, lw=1.6, color=color, alpha=0.55)

    vr = agg.get("vol_range_A3", float("nan"))
    mr = agg.get("mouth_122-232_range_A", float("nan"))
    ax.set_title(f"AOH1996 pocket volume — per-chain Cα convex hull | {struct}\n"
                 f"mean fluctuation range {vr:.0f} Å³   mouth open/close {mr:.1f} Å", fontsize=9)
    ax.set_xlabel("Time (ns)", fontsize=8)
    ax.set_ylabel("Pocket volume (Å³)", fontsize=8)
    ax.legend(fontsize=7, loc="upper right", framealpha=0.7, ncol=3)
    ax.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(out, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    print(f"  Saved {out.name}  (fluctuation range {vr:.0f} Å³)")


# ── figure C: DCCM heatmap (chain-averaged) ───────────────────────────────────

def fig_dccm(dccm_npy: Path, rmsf_json: Path, out: Path, dpi: int):
    dccm = np.load(str(dccm_npy))
    if dccm.size == 0:
        print("  SKIP DCCM: empty matrix")
        return
    N = dccm.shape[0]
    # pocket residue positions: the DCCM is indexed by within-chain Cα order.
    # We approximate index→resSeq as 1..N (mdtraj chain residue order) and mark
    # the scattered AOH residues individually (not one contiguous block).
    poc_idx = np.array([i for i in range(N) if (i + 1) in AOH_RESSEQ])

    fig, ax = plt.subplots(figsize=(5.6, 4.9))
    norm = TwoSlopeNorm(vmin=-1, vcenter=0, vmax=1)
    im = ax.imshow(dccm, cmap="RdBu_r", norm=norm, origin="upper", aspect="auto")
    plt.colorbar(im, ax=ax, label="DCCM coefficient", shrink=0.8)
    # mark each scattered pocket residue with a tick rather than one big box
    for p in poc_idx:
        ax.axhline(p, color="#111", lw=0.15, alpha=0.4)
        ax.axvline(p, color="#111", lw=0.15, alpha=0.4)
    if len(poc_idx) >= 2:
        sub = dccm[np.ix_(poc_idx, poc_idx)]
        off = sub[np.triu_indices(len(poc_idx), k=1)]
        poc_dccm = float(off.mean())
    else:
        poc_dccm = float("nan")
    ax.set_title(f"MD DCCM (chain-averaged) | {N} Cα residues\n"
                 f"Pocket internal DCCM (signed mean): {poc_dccm:.4f}", fontsize=9)
    ax.set_xlabel("Residue index (within chain)", fontsize=8)
    ax.set_ylabel("Residue index (within chain)", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.tight_layout(); fig.savefig(out, dpi=dpi, bbox_inches="tight"); plt.close(fig)
    print(f"  Saved {out.name}  (pocket internal DCCM={poc_dccm:.4f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()

    rmsf_json = RESULTS / "md_rmsf.json"
    vol_json  = RESULTS / "md_pocket_volume.json"
    dccm_npy  = RESULTS / "md_dccm.npy"
    anm_json  = RESULTS / "nma_apo_holo_comparison.json"

    print("Generating MD figures (corrected, per-chain)...")
    if check(rmsf_json, "RMSF"):
        fig_rmsf(rmsf_json, anm_json, RESULTS / "fig4a_md_rmsf.png", args.dpi)
    if check(vol_json, "pocket volume"):
        fig_pocket_volume(vol_json, RESULTS / "fig4b_md_pocket_vol.png", args.dpi)
    if check(dccm_npy, "DCCM") and check(rmsf_json, "RMSF"):
        fig_dccm(dccm_npy, rmsf_json, RESULTS / "fig4c_md_dccm.png", args.dpi)
    print("Done.")


if __name__ == "__main__":
    main()
