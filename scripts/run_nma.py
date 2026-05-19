"""
Anisotropic Network Model (ANM) flexibility analysis on apo PCNA (1W60).

Implements ANM from Atilgan et al. (2001) Biophys. J. 80:505-515.
Requires only NumPy + SciPy (no ProDy / MDAnalysis needed).

Outputs:
    data/results/nma_1W60.json  -- per-residue ANM-RMSF + DCCM summary
    data/results/nma_1W60_dccm.npy -- full N×N cross-correlation matrix

This analysis is a validated substitute for MD-derived RMSF when no
trajectory data is available. ANM captures the same slow-mode flexibility
and has been shown to correlate with MD RMSF at r~0.6-0.8 (Eyal et al. 2006,
Proteins 63:1072).

Usage:
    python scripts/run_nma.py
    python scripts/run_nma.py --pdb data/raw/1W60.pdb --cutoff 7.5 --n_modes 20
"""
from __future__ import annotations
import sys, json, argparse
from pathlib import Path

import numpy as np
from scipy.linalg import eigh

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

# AOH1996 ground-truth pocket residues defined by ZQZ contacts in 8GLA.
# ZQZ ligand is present ONLY on chains A and B in 8GLA (chains C/D carry no ligand).
# Chain C excluded to keep apo (1W60: A+B=48 res) and holo (8GLA: A+B=48 res) comparable.
AOH_GT_BY_CHAIN = {
    "A": {25,26,27,38,39,40,41,42,44,45,46,47,
          123,125,126,128,231,232,233,234,250,251,252,253},
    "B": {23,25,26,27,38,39,40,41,42,44,45,46,47,
          123,125,126,128,231,232,233,234,250,251,252},
}


# ── PDB Cα parser ─────────────────────────────────────────────────────────────

def parse_ca(pdb_path: Path) -> tuple[np.ndarray, list[dict]]:
    """Return Cα coords (N,3) and metadata list [{chain, resid, resname}]."""
    coords, meta = [], []
    seen = set()
    with open(pdb_path) as f:
        for line in f:
            if not line.startswith(("ATOM  ", "HETATM")):
                continue
            atom_name = line[12:16].strip()
            if atom_name != "CA":
                continue
            chain   = line[21].strip() or "A"
            resid   = int(line[22:26].strip())
            resname = line[17:20].strip()
            key = (chain, resid)
            if key in seen:
                continue
            seen.add(key)
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
            coords.append([x, y, z])
            meta.append({"chain": chain, "resid": resid, "resname": resname})
    return np.array(coords, dtype=np.float64), meta


# ── ANM core ──────────────────────────────────────────────────────────────────

def build_hessian(coords: np.ndarray, cutoff: float) -> np.ndarray:
    """Build 3N×3N ANM Hessian (spring constant γ=1 everywhere)."""
    n = len(coords)
    H = np.zeros((3 * n, 3 * n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1, n):
            d = coords[j] - coords[i]          # (3,)
            r2 = float(d @ d)
            if r2 > cutoff ** 2:
                continue
            outer = np.outer(d, d) / r2        # 3×3 super-element
            H[3*i:3*i+3, 3*j:3*j+3] -= outer
            H[3*j:3*j+3, 3*i:3*i+3] -= outer
            H[3*i:3*i+3, 3*i:3*i+3] += outer
            H[3*j:3*j+3, 3*j:3*j+3] += outer
    return H


def compute_anm(coords: np.ndarray, cutoff: float = 7.5, n_modes: int = 20
                ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns:
        msf     (N,)     per-residue mean-square fluctuation
        dccm    (N,N)    dynamic cross-correlation matrix
        eigvals (n_modes,) eigenvalues of used modes
    """
    n = len(coords)
    H = build_hessian(coords, cutoff)

    # For multi-chain / multi-fragment structures there may be many near-zero modes.
    # Scan the low end of the spectrum to find the spectral gap, then use modes
    # above the gap.  We probe the first 3N//4 modes at most.
    n_probe = min(3 * n, 3 * n // 4 + n_modes + 50)
    eigvals_all, eigvecs_all = eigh(H, subset_by_index=[0, n_probe - 1])

    # Threshold: first eigenvalue at least 100× larger than the 0th one's |magnitude|
    # OR absolute threshold 1e-4 — whichever is tighter.
    abs_threshold = max(1e-4, abs(eigvals_all[0]) * 100)
    nontrivial = np.where(eigvals_all > abs_threshold)[0]
    if len(nontrivial) < n_modes:
        raise ValueError(
            f"Too few non-trivial modes ({len(nontrivial)}) above threshold {abs_threshold:.2e}. "
            f"Try reducing n_modes or cutoff."
        )
    use_idx = nontrivial[:n_modes]
    eigvals = eigvals_all[use_idx]
    eigvecs = eigvecs_all[:, use_idx]
    # eigvecs: (3N, n_modes)

    inv_vals = 1.0 / eigvals   # (n_modes,)

    # Per-residue MSF: sum_k (1/λ_k) * ||v_k[3i:3i+3]||²
    msf = np.zeros(n)
    for k in range(n_modes):
        v = eigvecs[:, k].reshape(n, 3)
        msf += inv_vals[k] * (v ** 2).sum(axis=1)

    # DCCM: C_ij = <Δr_i·Δr_j> / sqrt(<Δr_i²><Δr_j²>)
    # <Δr_i·Δr_j> = sum_k (1/λ_k) * (v_k[3i:3i+3] · v_k[3j:3j+3])
    cross = np.zeros((n, n))
    for k in range(n_modes):
        v = eigvecs[:, k].reshape(n, 3)
        dot_ij = v @ v.T           # (N,N) dot products
        cross += inv_vals[k] * dot_ij

    denom = np.sqrt(np.maximum(np.outer(msf, msf), 0.0))
    denom[denom == 0] = 1.0
    dccm = cross / denom
    np.clip(dccm, -1.0, 1.0, out=dccm)

    return msf, dccm, eigvals


# ── Main ──────────────────────────────────────────────────────────────────────

def run(pdb_path: Path, cutoff: float, n_modes: int) -> dict:
    print(f"Parsing {pdb_path.name} ...")
    coords, meta = parse_ca(pdb_path)
    n = len(coords)
    print(f"  {n} Ca atoms")

    print(f"Building ANM Hessian (cutoff={cutoff} A) ...")
    msf, dccm, eigvals = compute_anm(coords, cutoff=cutoff, n_modes=n_modes)

    msf = np.maximum(msf, 0.0)   # guard against floating-point negatives
    rmsf = np.sqrt(msf)
    mean_rmsf = rmsf.mean()
    scale = (1.0 / mean_rmsf) if mean_rmsf > 0 else 1.0
    rmsf_norm = rmsf * scale

    # Label pocket membership (AOH1996 residues)
    aoh_mask = np.array([
        meta[i]["resid"] in AOH_GT_BY_CHAIN.get(meta[i]["chain"], set())
        for i in range(n)
    ])

    # Save full DCCM
    stem = pdb_path.stem.upper()
    dccm_path = REPO / "data" / "results" / f"nma_{stem}_dccm.npy"
    dccm_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(dccm_path), dccm.astype(np.float32))
    print(f"Saved DCCM -> {dccm_path.relative_to(REPO)}")

    # Pocket vs background stats
    pocket_rmsf  = float(rmsf_norm[aoh_mask].mean())  if aoh_mask.any() else None
    bg_rmsf      = float(rmsf_norm[~aoh_mask].mean()) if (~aoh_mask).any() else None
    fold_change  = round(pocket_rmsf / bg_rmsf, 3)    if (pocket_rmsf and bg_rmsf) else None

    # Pocket DCCM: mean absolute internal correlation among AOH residues
    pocket_idx = np.where(aoh_mask)[0]
    if len(pocket_idx) >= 2:
        sub = dccm[np.ix_(pocket_idx, pocket_idx)]
        off_diag = sub[np.triu_indices(len(pocket_idx), k=1)]
        pocket_internal_corr = float(off_diag.mean())
    else:
        pocket_internal_corr = None

    # Per-residue records
    residues_out = []
    for i, m in enumerate(meta):
        residues_out.append({
            "chain": m["chain"],
            "resid": m["resid"],
            "resname": m["resname"],
            "anm_msf": round(float(msf[i]), 6),
            "anm_rmsf_norm": round(float(rmsf_norm[i]), 4),
            "in_aoh_pocket": bool(aoh_mask[i]),
        })

    result = {
        "method": "Anisotropic Network Model (ANM)",
        "reference": "Atilgan et al. (2001) Biophys. J. 80:505-515",
        "structure": pdb_path.name,
        "n_residues": n,
        "cutoff_angstrom": cutoff,
        "n_modes_used": n_modes,
        "note": (
            "RMSF values are in relative units (normalized to mean=1.0). "
            "ANM spring constant γ is set uniformly; absolute magnitudes are not comparable "
            "to MD-RMSF in Å. Fold-change and DCCM values are γ-independent."
        ),
        "aoh_pocket_analysis": {
            "n_aoh_residues": int(aoh_mask.sum()),
            "pocket_mean_rmsf_norm": round(pocket_rmsf, 4) if pocket_rmsf else None,
            "background_mean_rmsf_norm": round(bg_rmsf, 4) if bg_rmsf else None,
            "fold_change_pocket_vs_bg": fold_change,
            "interpretation": (
                "Pocket residues show elevated flexibility vs background "
                f"(fold-change {fold_change:.2f}×). "
                "This is consistent with the site being a cryptic pocket — "
                "intrinsically flexible in the apo state."
            ) if fold_change and fold_change > 1.0 else (
                "Pocket residues show similar or reduced flexibility vs background — "
                "may indicate rigid cryptic pocket or classification artefact."
            ),
            "pocket_internal_dccm": round(pocket_internal_corr, 4) if pocket_internal_corr is not None else None,
            "dccm_interpretation": (
                "Positive internal DCCM among AOH1996 pocket residues — "
                "residues move coherently, consistent with a collective opening motion."
            ) if pocket_internal_corr and pocket_internal_corr > 0 else None,
        },
        "eigenvalues": [round(float(v), 6) for v in eigvals[:10]],
        "dccm_file": f"data/results/nma_{stem}_dccm.npy",
        "residues": residues_out,
    }

    out_path = REPO / "data" / "results" / f"nma_{stem}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved NMA results -> {out_path.relative_to(REPO)}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdb",      default="data/raw/1W60.pdb")
    parser.add_argument("--cutoff",   type=float, default=7.5)
    parser.add_argument("--n_modes",  type=int,   default=20)
    args = parser.parse_args()

    result = run(Path(args.pdb), args.cutoff, args.n_modes)

    a = result["aoh_pocket_analysis"]
    print("\n-- ANM Pocket Analysis ----------------------------------")
    print(f"  AOH1996 residues analysed : {a['n_aoh_residues']}")
    print(f"  Pocket RMSF (norm)        : {a['pocket_mean_rmsf_norm']:.4f}")
    print(f"  Background RMSF (norm)    : {a['background_mean_rmsf_norm']:.4f}")
    print(f"  Fold-change               : {a['fold_change_pocket_vs_bg']:.3f}×")
    print(f"  Internal DCCM             : {a['pocket_internal_dccm']:.4f}")
    print(f"\n  {a['interpretation']}")


if __name__ == "__main__":
    main()
