#!/usr/bin/env python
"""Phase 5 1AXC — pocket-dynamics metrics (geometry, not just CA RMSF).

Answers 'does the pocket have dynamics' with metrics RMSF alone cannot give:
  - heavy-atom RMSF (sidechain gating, not just backbone)
  - per-region SASA time series (opening = SASA increases / fluctuates)
  - per-region radius of gyration time series (breathing)
  - front-face pocket cross-wall CA distances (mouth opening/closing)

Exploratory triage only. rep1 (full 25 ns) only; 5 ns equilibration discarded.
Computed per monomer (chains 0/1/2) as informal triplicates. METRICS ONLY — any
supports/weakens conclusion is gated on human MD-interpretation review (doc 26).

Metric caveats (do NOT over-read):
  - Region radius of gyration for the small contiguous candidate/reference
    windows (< ~8 residues) is covalently fixed and nearly constant; it is NOT a
    pocket-breathing signal. Flagged non-informative (rg_informative=False) and
    blanked in the headline table; raw values stay in the CSV.
  - Region-SUMMED SASA (and its coefficient of variation) dilutes a single
    opening residue with buried, invariant neighbours. sasa_std_A2 / sasa_range_A2
    carry the opening signal undiluted; the per-residue proxy max_res_sasa_std_A2
    (max over the region of each residue's SASA std) is reported alongside, and
    the dilution-prone sasa_cv is dropped from the headline table.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd, mdtraj as md

RUN = Path("outputs/phase5_md/time_crunch_1axc_25ns")
REP = RUN / "replicate_01"
EQUIL_FRAMES = 50          # 5 ns @ 0.1 ns/frame
NS_PER_FRAME = 0.1
OUT = RUN / "analysis_fixed"
OUT.mkdir(parents=True, exist_ok=True)

def expand(spec):
    out = []
    for part in spec:
        a, b = part.split("-"); out += list(range(int(a), int(b) + 1))
    return sorted(set(out))

REGIONS = {
    "front_face_pip_pocket": expand(["40-44", "117-135", "230-235", "251-253"]),
    "cand_239-243": expand(["239-243"]),
    "cand_28-32":   expand(["28-32"]),
    "cand_206-210": expand(["206-210"]),
    "cand_134-138": expand(["134-138"]),
    "ref_118-122":  expand(["118-122"]),
}
# canonical front-face cross-wall CA pairs (pocket mouth)
CROSS_PAIRS = [(44, 251), (122, 232), (128, 252), (42, 234)]

print("loading rep1 ...")
traj = md.load_dcd(str(REP / "trajectory.dcd"), top=str(REP / "solvated_initial.pdb"))
traj.make_molecules_whole(inplace=True)
traj.image_molecules(inplace=True)

# protein-only copy for SASA/Rg speed
prot_idx = traj.topology.select("protein")
prot = traj.atom_slice(prot_idx)
# align protein on core CA (exclude analyzed regions) to remove rigid drift
analyzed = set(sum(REGIONS.values(), []))
core_ca = prot.topology.select(
    "name CA and protein and not (resSeq " + " ".join(str(r) for r in sorted(analyzed)) + ")")
prot.superpose(prot, 0, atom_indices=core_ca)
prot = prot[EQUIL_FRAMES:]
n = prot.n_frames
print(f"frames after equil: {n}")

chains = sorted({r.chain.index for r in prot.topology.residues if r.is_protein})
print("protein chains:", chains)

# per-residue SASA once (mode='residue'): shape (frames, n_residues)
print("computing SASA (Shrake-Rupley) ...")
sasa = md.shrake_rupley(prot, mode="residue")        # nm^2
res_list = list(prot.topology.residues)
resindex_of = {r.index: i for i, r in enumerate(res_list)}

def region_res_indices(ch, resseqs):
    s = set(resseqs)
    return [r.index for r in prot.topology.residues
            if r.is_protein and r.chain.index == ch and int(r.resSeq) in s]

rows, sasa_ts_rows = [], []
for name, resseqs in REGIONS.items():
    for ch in chains:
        ridx = region_res_indices(ch, resseqs)
        if not ridx:
            continue
        heavy = prot.topology.select(
            "chainid %d and not element H and (resSeq %s)"
            % (ch, " ".join(str(r) for r in resseqs)))
        # heavy-atom RMSF about mean
        xyz = prot.xyz[:, heavy, :]
        rmsf = np.sqrt(np.mean(np.sum((xyz - xyz.mean(0)) ** 2, axis=2), axis=0))
        # region SASA per frame, nm^2 -> A^2
        cols = [resindex_of[i] for i in ridx]
        per_res_sasa = sasa[:, cols] * 100.0          # (frames, n_res) in A^2
        reg_sasa = per_res_sasa.sum(axis=1)           # region SUM (dilutes opening)
        # CAVEAT: a region SUM (and its CV) buries a single opening residue under
        # neighbouring invariant/buried residues. sasa_std_A2 and sasa_range_A2
        # carry the opening signal undiluted; sasa_cv (region-sum coefficient of
        # variation) is dilution-prone, so also report the per-residue fluctuation
        # (max over the region of each residue's SASA std) as the undiluted proxy.
        per_res_sasa_std = per_res_sasa.std(axis=0)   # (n_res,)
        max_res_sasa_std = (float(per_res_sasa_std.max())
                            if per_res_sasa_std.size else float("nan"))
        # region Rg (heavy atoms) per frame. NOTE: for a short contiguous segment
        # (< ~8 residues) Rg is covalently fixed and nearly constant -> NOT a
        # pocket-breathing signal; flagged non-informative via rg_informative.
        sub = prot.atom_slice(heavy)
        rg = md.compute_rg(sub) * 10.0  # nm -> A
        rg_informative = len(ridx) >= 8
        rows.append({
            "region": name, "chain": ch, "n_res": len(ridx),
            "heavy_rmsf_mean_A": float(np.mean(rmsf) * 10),
            "heavy_rmsf_max_A": float(np.max(rmsf) * 10),
            "sasa_mean_A2": float(reg_sasa.mean()),
            "sasa_std_A2": float(reg_sasa.std()),
            "sasa_cv": float(reg_sasa.std() / reg_sasa.mean()) if reg_sasa.mean() else float("nan"),
            "sasa_cv_caveat": "region-sum CV dilutes single-residue opening; see max_res_sasa_std_A2",
            "max_res_sasa_std_A2": max_res_sasa_std,
            "sasa_range_A2": float(reg_sasa.max() - reg_sasa.min()),
            "rg_mean_A": float(rg.mean()),
            "rg_std_A": float(rg.std()),
            "rg_informative": bool(rg_informative),
        })
        for fi in range(n):
            sasa_ts_rows.append({"region": name, "chain": ch, "frame": fi + EQUIL_FRAMES,
                                 "time_ns": (fi + EQUIL_FRAMES) * NS_PER_FRAME,
                                 "sasa_A2": float(reg_sasa[fi])})

df = pd.DataFrame(rows)
df.to_csv(OUT / "pocket_dynamics_summary.csv", index=False)
pd.DataFrame(sasa_ts_rows).to_csv(OUT / "pocket_sasa_timeseries.csv", index=False)

# cross-wall CA distances (per chain), front-face pocket mouth
dist_rows = []
for ch in chains:
    for a, b in CROSS_PAIRS:
        ia = prot.topology.select(f"chainid {ch} and resSeq {a} and name CA")
        ib = prot.topology.select(f"chainid {ch} and resSeq {b} and name CA")
        if len(ia) == 0 or len(ib) == 0:
            continue
        d = md.compute_distances(prot, [[ia[0], ib[0]]])[:, 0] * 10.0  # A
        dist_rows.append({"chain": ch, "pair": f"{a}-{b}",
                          "mean_A": float(d.mean()), "std_A": float(d.std()),
                          "min_A": float(d.min()), "max_A": float(d.max()),
                          "range_A": float(d.max() - d.min())})
dist_df = pd.DataFrame(dist_rows)
dist_df.to_csv(OUT / "pocket_crosswall_distances.csv", index=False)

pd.set_option("display.width", 200, "display.max_columns", 20)
print("\n=== PER-REGION DYNAMICS (rep1, 3 monomers) ===")
agg = df.groupby("region").agg(
    n_res=("n_res", "first"),
    heavy_rmsf_A=("heavy_rmsf_mean_A", "mean"),
    sasa_mean_A2=("sasa_mean_A2", "mean"),
    sasa_std_A2=("sasa_std_A2", "mean"),
    sasa_range_A2=("sasa_range_A2", "mean"),
    max_res_sasa_std_A2=("max_res_sasa_std_A2", "mean"),
    rg_std_A=("rg_std_A", "mean"),
    rg_informative=("rg_informative", "first"),
).reset_index()
# Rg of a short contiguous segment is covalently fixed (non-informative); blank
# it in the headline so it is not misread as pocket breathing. Full values remain
# in pocket_dynamics_summary.csv alongside the rg_informative flag.
agg.loc[~agg["rg_informative"], "rg_std_A"] = float("nan")
print(agg.to_string(index=False))
print("NOTE: rg_std_A blanked for regions < 8 residues (covalently fixed, "
      "non-informative). sasa_cv omitted here (region-sum CV dilutes single-"
      "residue opening); use max_res_sasa_std_A2 as the undiluted per-residue "
      "proxy. Full sasa_cv / rg values remain in pocket_dynamics_summary.csv.")
print("\n=== FRONT-FACE POCKET CROSS-WALL CA DISTANCES (mean over chains) ===")
if not dist_df.empty:
    print(dist_df.groupby("pair").agg(mean_A=("mean_A", "mean"), std_A=("std_A", "mean"),
                                      range_A=("range_A", "mean")).reset_index().to_string(index=False))
print(f"\nOutputs -> {OUT}")
