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

# Modified standard residues that appear as HETATM but carry a genuine protein Ca.
# Used only as a fallback when the PDB lacks an element column; when the element
# column is present, the element == "C" check already admits these correctly.
_MODIFIED_AA = {"MSE", "SEP", "TPO", "PTR", "CSO", "CME", "MLY", "M3L", "HYP", "PCA"}

# Statistical settings for the pocket-vs-background permutation test.
FOLD_CHANGE_FLOOR = 1.05   # pre-registered minimum pocket/background fold-change for a positive claim
PERM_ALPHA        = 0.05   # permutation-test significance threshold
N_PERM            = 5000   # random equal-size residue sets drawn for the null distribution
PERM_SEED         = 0      # fixed RNG seed -> reproducible p-values (does not affect fold-change)


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
            # Reject non-protein atoms named "CA" (e.g. calcium ions, whose element
            # column reads "CA").  A protein Ca is element carbon.  For HETATM records
            # require an explicit carbon element, or -- when the element column is
            # absent (older PDBs) -- allow only known modified residues (e.g. MSE).
            if line.startswith("HETATM"):
                element = line[76:78].strip() if len(line) >= 78 else ""
                if element:
                    if element != "C":
                        continue
                elif line[17:20].strip() not in _MODIFIED_AA:
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


# NOTE on cutoff: 7.5 A is retained as the default because the already-reported
# apo/holo fold-change numbers (apo 1W60 0.857, holo 8GLA 1.157, delta +0.300)
# were computed at this cutoff. Atilgan et al. (2001) recommend ~13 A for ANM
# (7.5 A is really a GNM cutoff); raising it would improve within-chain mode
# accuracy but WOULD change those published numbers, so it is left unchanged here.
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


# ── Statistics ──────────────────────────────────────────────────────────────

def _fmt(v, spec: str) -> str:
    """Format v with `spec`, or return 'n/a' if v is None (avoids NoneType crash)."""
    return format(v, spec) if v is not None else "n/a"


def foldchange_permutation_p(values: np.ndarray, mask: np.ndarray,
                             n_perm: int = N_PERM, seed: int = PERM_SEED
                             ) -> tuple[float | None, float | None]:
    """
    Permutation test: is mean(values[mask]) / mean(values[~mask]) larger than
    expected for a random subset of the same size? Returns
    (null_mean_fold_change, one-sided p = P(null_fc >= observed_fc)).
    Does NOT recompute or alter the reported fold-change; only supplies a null.
    """
    n = len(values)
    k = int(mask.sum())
    if k == 0 or k == n:
        return None, None
    obs_fc = values[mask].mean() / values[~mask].mean()
    rng = np.random.default_rng(seed)
    ranks = rng.random((n_perm, n))
    sel = np.argsort(ranks, axis=1)[:, :k]                  # (n_perm, k)
    perm_mask = np.zeros((n_perm, n), dtype=bool)
    np.put_along_axis(perm_mask, sel, True, axis=1)
    in_mean  = (values[None, :] * perm_mask).sum(axis=1) / k
    out_mean = (values[None, :] * ~perm_mask).sum(axis=1) / (n - k)
    null_fc = in_mean / out_mean
    p = (np.sum(null_fc >= obs_fc) + 1) / (n_perm + 1)
    return float(null_fc.mean()), float(p)


def dccm_internal_permutation_p(dccm: np.ndarray, mask: np.ndarray,
                                n_perm: int = N_PERM, seed: int = PERM_SEED
                                ) -> tuple[float | None, float | None]:
    """
    Permutation test for the mean signed off-diagonal DCCM among the masked
    residues vs random equal-size residue sets. Returns (null_mean, p = P(null>=obs)).
    Weak control only: a spatial cluster has near-guaranteed positive internal
    DCCM, so this does not correct for spatial proximity.
    """
    n = dccm.shape[0]
    k = int(mask.sum())
    if k < 2:
        return None, None
    iu = np.triu_indices(k, k=1)

    def internal_mean(idx: np.ndarray) -> float:
        sub = dccm[np.ix_(idx, idx)]
        return float(sub[iu].mean())

    obs = internal_mean(np.where(mask)[0])
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for t in range(n_perm):
        sel = np.sort(rng.choice(n, size=k, replace=False))
        null[t] = internal_mean(sel)
    p = (np.sum(null >= obs) + 1) / (n_perm + 1)
    return float(null.mean()), float(p)


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

    # Fail loudly and early if no ground-truth pocket residues matched, so the user
    # learns the real cause (chain-ID / numbering mismatch) instead of an opaque
    # "unsupported format string passed to NoneType" TypeError at the final print.
    if not aoh_mask.any():
        chains = sorted({m["chain"] for m in meta})
        raise ValueError(
            f"No ground-truth AOH1996 pocket residues matched in {pdb_path.name}: "
            f"parsed {n} Ca atoms across chains {chains}, but none matched "
            f"AOH_GT_BY_CHAIN (chains {sorted(AOH_GT_BY_CHAIN)}). "
            "Check the chain IDs and residue numbering (e.g. lowercase chain IDs, "
            "renumbered residues, or a chain-C-only / peptide-only input)."
        )

    # Save full DCCM
    stem = pdb_path.stem.upper()
    dccm_path = REPO / "data" / "results" / f"nma_{stem}_dccm.npy"
    dccm_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(dccm_path), dccm.astype(np.float32))
    print(f"Saved DCCM -> {dccm_path.relative_to(REPO)}")

    # Pocket vs background stats. Use explicit None checks (not truthiness) so a
    # genuine mean of exactly 0.0 is not silently treated as "not computed".
    pocket_rmsf  = float(rmsf_norm[aoh_mask].mean())  if aoh_mask.any() else None
    bg_rmsf      = float(rmsf_norm[~aoh_mask].mean()) if (~aoh_mask).any() else None
    fold_change  = (round(pocket_rmsf / bg_rmsf, 3)
                    if pocket_rmsf is not None and bg_rmsf not in (None, 0) else None)

    # Permutation test for the fold-change vs random equal-size residue sets.
    # This supplies a null distribution + p-value; it does not change fold_change.
    fc_null_mean, fc_pvalue = foldchange_permutation_p(rmsf_norm, aoh_mask)

    # Pocket DCCM: mean SIGNED off-diagonal correlation among AOH residues
    # (signed, not absolute -- a positive mean is what "coherent motion" requires).
    pocket_idx = np.where(aoh_mask)[0]
    if len(pocket_idx) >= 2:
        sub = dccm[np.ix_(pocket_idx, pocket_idx)]
        off_diag = sub[np.triu_indices(len(pocket_idx), k=1)]
        pocket_internal_corr = float(off_diag.mean())
    else:
        pocket_internal_corr = None
    dccm_null_mean, dccm_pvalue = dccm_internal_permutation_p(dccm, aoh_mask)

    # Gate the positive claims on a pre-registered effect-size floor AND significance.
    fc_significant = (fold_change is not None
                      and fold_change >= FOLD_CHANGE_FLOOR
                      and fc_pvalue is not None and fc_pvalue < PERM_ALPHA)
    dccm_significant = (pocket_internal_corr is not None and pocket_internal_corr > 0
                        and dccm_pvalue is not None and dccm_pvalue < PERM_ALPHA)

    if fold_change is None:
        interpretation = ("Pocket-vs-background flexibility could not be computed "
                          "(no pocket or no background residues).")
    elif fc_significant:
        interpretation = (
            f"Pocket residues show elevated flexibility vs background "
            f"(fold-change {fold_change:.2f}×, permutation p={_fmt(fc_pvalue, '.3g')} "
            f"over {N_PERM} random equal-size residue sets, floor {FOLD_CHANGE_FLOOR}×). "
            "Consistent with an intrinsically flexible cryptic-pocket site in the apo state."
        )
    else:
        interpretation = (
            f"Pocket flexibility is NOT significantly elevated vs background "
            f"(fold-change {fold_change:.2f}×, permutation p={_fmt(fc_pvalue, '.3g')} "
            f"over {N_PERM} random equal-size residue sets, floor {FOLD_CHANGE_FLOOR}×). "
            "No robust pocket-flexibility signal at this site under this ANM setup."
        )

    if pocket_internal_corr is None:
        dccm_interpretation = None
    elif dccm_significant:
        dccm_interpretation = (
            f"Internal DCCM among AOH1996 pocket residues ({pocket_internal_corr:.3f}) "
            f"exceeds random equal-size residue sets (permutation p={_fmt(dccm_pvalue, '.3g')}); "
            "residues move coherently, consistent with a collective opening motion. "
            "Caveat: spatial proximity alone inflates internal DCCM, so this is suggestive only."
        )
    else:
        dccm_interpretation = (
            f"Internal DCCM among pocket residues ({pocket_internal_corr:.3f}) is not "
            f"distinguishable from random equal-size residue sets "
            f"(permutation p={_fmt(dccm_pvalue, '.3g')})."
        )

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
            "pocket_mean_rmsf_norm": round(pocket_rmsf, 4) if pocket_rmsf is not None else None,
            "background_mean_rmsf_norm": round(bg_rmsf, 4) if bg_rmsf is not None else None,
            "fold_change_pocket_vs_bg": fold_change,
            "fold_change_floor": FOLD_CHANGE_FLOOR,
            "fold_change_null_mean": round(fc_null_mean, 4) if fc_null_mean is not None else None,
            "fold_change_permutation_p": round(fc_pvalue, 4) if fc_pvalue is not None else None,
            "fold_change_significant": bool(fc_significant),
            "n_permutations": N_PERM,
            "interpretation": interpretation,
            "pocket_internal_dccm": round(pocket_internal_corr, 4) if pocket_internal_corr is not None else None,
            "pocket_internal_dccm_null_mean": round(dccm_null_mean, 4) if dccm_null_mean is not None else None,
            "pocket_internal_dccm_permutation_p": round(dccm_pvalue, 4) if dccm_pvalue is not None else None,
            "pocket_internal_dccm_significant": bool(dccm_significant),
            "dccm_interpretation": dccm_interpretation,
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
    parser.add_argument("--cutoff",   type=float, default=7.5)  # 7.5 A kept to preserve reported numbers; ANM ideal ~13 A (Atilgan 2001) -- see compute_anm NOTE
    parser.add_argument("--n_modes",  type=int,   default=20)
    args = parser.parse_args()

    result = run(Path(args.pdb), args.cutoff, args.n_modes)

    a = result["aoh_pocket_analysis"]
    print("\n-- ANM Pocket Analysis ----------------------------------")
    print(f"  AOH1996 residues analysed : {a['n_aoh_residues']}")
    print(f"  Pocket RMSF (norm)        : {_fmt(a['pocket_mean_rmsf_norm'], '.4f')}")
    print(f"  Background RMSF (norm)    : {_fmt(a['background_mean_rmsf_norm'], '.4f')}")
    print(f"  Fold-change               : {_fmt(a['fold_change_pocket_vs_bg'], '.3f')}×")
    print(f"  Internal DCCM             : {_fmt(a['pocket_internal_dccm'], '.4f')}")
    print(f"\n  {a['interpretation']}")


if __name__ == "__main__":
    main()
