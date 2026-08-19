#!/usr/bin/env python
"""
PBC-correct analysis + positive-control comparison for the PCNA MD validation (v2).

Reads outputs/{APO,CONTROL}/rep*/production.dcd (topology = system_solvated.pdb) and:
  1. Images periodic boundaries BEFORE superposition  (fixes the old 25-A RMSD artifact).
  2. Superposes on a stable core = protein Ca EXCLUDING the pocket (no circularity).
  3. RMSF about the MEAN position, after discarding equilibration.
  4. Pocket-openness proxies: pocket SASA, pocket-Ca radius of gyration.
  5. POSITIVE CONTROL: is the CONTROL (open) pocket measurably larger than the APO (closed)
     pocket? If NOT, the method/sampling can't see opening and a "no-opening" apo result is
     UNINTERPRETABLE - not a real negative. This is the gate that stops a false negative.

  === v2 changes (2026-07 biological-validity audit) ===
  * Pocket residues + apo/control PDBs + interface chains come from pockets/<name>.json
    (single source of truth shared with run_md.py; the old hand-curated list that dropped
    IDCL contacts 121/124/129/131 is gone).
  * PBC-artifact detection is now a frame-to-frame JUMP detector (a box-hop is a spike), not a
    blanket 0.6 nm cap that also trips on legitimate large-amplitude motion. Smooth large drift
    is reported separately as info, not a failure.
  * Reads prep_audit.json and surfaces low-resolution / rebuilt-residue caveats in the report
    (e.g. 8GLA is 3.77 A) so a PASS/FAIL is never read without that context.

Outputs: outputs/analysis/{summary.json, per_replicate.csv, REPORT.md, *.png}
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EQUIL_NS = 5.0  # discard before RMSF/pocket stats
PBC_JUMP_NM = 0.30   # frame-to-frame backbone RMSD jump above which a PBC/imaging artifact is suspected
DRIFT_INFO_NM = 0.60  # smooth drift above this is reported (info only, NOT a failure)
CONTROL_MIN_REPLICATES = 3
CONTROL_MIN_NS = 5.0
CONTROL_MIN_RMSF_NM = 0.015
CONTROL_MIN_OPEN_LIKE_FRACTION = 0.20
DIAGNOSTIC_MARK = "DIAGNOSTIC_ONLY - NOT_FOR_SCIENTIFIC_INTERPRETATION"


def load_pocket(name: str) -> dict:
    p = HERE / "pockets" / f"{name}.json"
    if not p.exists():
        sys.exit(f"No pocket definition at {p}.")
    return json.loads(p.read_text())


def _imports():
    try:
        import mdtraj as md, numpy as np, pandas as pd
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except Exception as exc:
        sys.exit("Missing deps. `conda activate pcna-md-4070` first. (%s)" % exc)
    return md, np, pd, plt


def pocket_selection(top, resseqs, interface_chain_indices, allow_keys=None):
    """Atom indices of pocket residues on the interface chains (by chain ORDER, post-assembly).

    ``allow_keys``, when given, is an explicit set of ``(chain_index, resSeq)`` pairs and
    overrides the chain x resseq product. Pass the apo/control INTERSECTION here so both
    trajectories are measured over the identical atom set -- see :func:`resolved_pocket_keys`.
    """
    want_chains = set(interface_chain_indices)
    resset = set(resseqs)
    sel = []
    for a in top.atoms:
        if allow_keys is not None:
            if (a.residue.chain.index in want_chains and a.residue.resSeq in resset
                    and (a.residue.chain.index, a.residue.resSeq, a.name) in allow_keys):
                sel.append(a.index)
        elif a.residue.chain.index in want_chains and a.residue.resSeq in resset:
            sel.append(a.index)
    return sorted(sel)


def resolved_pocket_keys(top, resseqs, interface_chain_indices):
    """The ``(chain_index, resSeq, atom_name)`` pocket ATOMS present in this topology.

    Atom-level, not residue-level, deliberately. SASA is a per-atom quantity, and apo and
    control were measured to resolve the SAME 56 pocket residues but 854 vs 855 atoms --
    protonation and terminal/rebuilt side-chain differences survive a residue-level check.
    """
    want_chains = set(interface_chain_indices)
    resset = set(resseqs)
    return {(a.residue.chain.index, a.residue.resSeq, a.name) for a in top.atoms
            if a.residue.chain.index in want_chains and a.residue.resSeq in resset}


def resolved_pocket_residues(top, resseqs, interface_chain_indices):
    """The ``(chain_index, resSeq)`` pocket residues present -- for human-readable reporting."""
    return {(c, r) for c, r, _ in resolved_pocket_keys(top, resseqs, interface_chain_indices)}


def _protein_top(md, top_pdb: Path):
    """Protein-only topology, matching the slice analyze_replicate performs."""
    t = md.load(str(top_pdb))
    return t.atom_slice(t.top.select("protein")).top


def terminal_or_gap_adjacent(top):
    """``(chain_index, resSeq)`` residues at a chain end or beside a numbering gap.

    Their solvent exposure is dominated by bookkeeping, not by pocket conformation: a
    residue that is internal in one structure and a chain terminus in the other gains a
    whole exposed face plus an OXT. Measured on the real prepared assemblies, residue 254
    LYS was 0.920 nm^2 in apo (internal) but 2.416 nm^2 in the control (chain end) -- a
    +1.496 nm^2 difference from terminus status alone, against only +0.435 nm^2 of genuine
    structural difference summed over the other 22 pocket residues. Differencing those is
    measuring where the crystal stopped, not whether the pocket opened.
    """
    out = set()
    for ch in top.chains:
        res = sorted(ch.residues, key=lambda r: r.resSeq)
        if not res:
            continue
        out.add((ch.index, res[0].resSeq))
        out.add((ch.index, res[-1].resSeq))
        for a, b in zip(res, res[1:]):
            if b.resSeq - a.resSeq > 1:            # unresolved loop between them
                out.add((ch.index, a.resSeq))
                out.add((ch.index, b.resSeq))
    return out


def pocket_parity(md, role_tops: dict, resseqs, iface, min_coverage=0.80,
                  exclude_termini=True):
    """Intersect the pocket residues resolved in every role's topology.

    Apo and control are DIFFERENT crystal structures with different unmodelled regions --
    8GLA (3.77 A) lacks residues 1W60 resolves. Measuring pocket SASA over different atom
    sets makes ``control - apo`` a comparison of two different pockets: the missing
    residue's own SASA enters as an additive bias, which was large enough to INVERT the
    sign of the positive-control gate at analyze_md.py's ``holo.mean() > apo.mean()``.

    Returns ``(allow_keys, report)``. Hard-fails below ``min_coverage`` because past that
    point the intersection is no longer the pocket the GNN identified.
    """
    per_role = {role: resolved_pocket_keys(top, resseqs, iface) for role, top in role_tops.items()}
    common = set.intersection(*per_role.values()) if per_role else set()
    union = set().union(*per_role.values()) if per_role else set()

    excluded_termini = set()
    if exclude_termini and role_tops:
        bad_res = set().union(*(terminal_or_gap_adjacent(t) for t in role_tops.values()))
        excluded_termini = {(c, s) for c, s, _ in common if (c, s) in bad_res}
        if excluded_termini:
            common = {k for k in common if (k[0], k[1]) not in bad_res}
            print(f"[parity] excluding {len(excluded_termini)} terminus/gap-adjacent residue(s) "
                  "whose SASA reflects where the crystal ends, not pocket opening: "
                  + ", ".join(f"chain{c}:{s}" for c, s in sorted(excluded_termini)))
            if not common:
                sys.exit("[parity] FATAL: every pocket residue is a chain terminus or beside an "
                         "unresolved gap. There is nothing left to measure. Re-derive the pocket "
                         "or pass --keep-termini and interpret the result with that caveat.")
    dropped = {role: sorted(keys - common) for role, keys in per_role.items()}
    coverage = (len(common) / len(union)) if union else 0.0
    res_per_role = {r: {(c, s) for c, s, _ in k} for r, k in per_role.items()}
    common_res = {(c, s) for c, s, _ in common}
    report = {
        "granularity": "atom (chain_index, resSeq, atom_name)",
        "per_role_atoms": {r: len(k) for r, k in per_role.items()},
        "per_role_residues": {r: len(k) for r, k in res_per_role.items()},
        "common_atoms": len(common), "union_atoms": len(union),
        "common_residues": len(common_res),
        "atom_coverage": round(coverage, 4),
        "excluded_terminus_or_gap_adjacent": sorted(f"chain{c}:{s}" for c, s in excluded_termini),
        "dropped_per_role": {r: [f"chain{c}:{s}:{n}" for c, s, n in d] for r, d in dropped.items()},
    }
    for role, d in dropped.items():
        if d:
            print(f"[parity] {role}: dropping {len(d)} atom(s) absent from another role: "
                  + ", ".join(f"chain{c}:{s}:{n}" for c, s, n in d[:12])
                  + (" ..." if len(d) > 12 else ""))
    if union and coverage < min_coverage:
        sys.exit(f"[parity] FATAL: apo/control share only {len(common)}/{len(union)} pocket "
                 f"atoms ({coverage:.0%} < {min_coverage:.0%}). The structures do not resolve "
                 f"the same pocket, so control-minus-apo would not be a comparison of the same "
                 f"site. Details: {json.dumps(report, indent=2)}")
    print(f"[parity] measuring both roles over {len(common)} shared atoms "
          f"({len(common_res)} residues, {coverage:.1%} of the union)")
    return common, report


def _resseqs(items):
    out = []
    for item in items or []:
        if isinstance(item, dict):
            out.append(int(item["resid"]))
        else:
            out.append(int(item))
    return out


def analysis_regions(pocket: dict) -> dict[str, list[int]]:
    """Frozen region groupings when present; fallback to a single pocket region."""
    core = _resseqs(pocket.get("core_3of3"))
    fringe2 = _resseqs(pocket.get("fringe_2of3"))
    fringe1 = _resseqs(pocket.get("uncertain_fringe_1of3"))
    supported = sorted(set(_resseqs(pocket.get("pocket_residues_resseq")) or (core + fringe2)))
    if core or fringe2 or fringe1:
        regions = {
            "core_3of3": sorted(set(core)),
            "supported_ge2of3": supported,
        }
        if fringe2:
            regions["supported_fringe_2of3"] = sorted(set(fringe2))
        if fringe1:
            regions["seed_specific_uncertain_fringe_1of3"] = sorted(set(fringe1))
            regions["full_union_exploratory"] = sorted(set(supported + fringe1))
        return {k: v for k, v in regions.items() if v}
    return {"pocket": sorted(set(_resseqs(pocket.get("pocket_residues_resseq"))))}


class HullDependencyUnavailable(RuntimeError):
    """scipy.spatial.ConvexHull could not be imported.

    This is deliberately an exception rather than a NaN. Before the 2026-08-16 repair
    ``convex_hull_volume_A3`` swallowed ImportError and returned NaN, so a machine without
    scipy produced ``openness = {"available": true, "open_like_fraction": 0.0}`` -- a missing
    optional dependency silently became the scientific claim "the pocket never opened".
    A metric that cannot be computed must be UNAVAILABLE, not zero.
    """


def hull_backend_available() -> tuple[bool, str]:
    """Whether the convex-hull backend can be imported at all (dependency, not geometry)."""
    try:
        from scipy.spatial import ConvexHull  # noqa: F401
        return True, "scipy.spatial.ConvexHull available"
    except Exception as exc:
        return False, f"scipy.spatial.ConvexHull unavailable: {type(exc).__name__}: {exc}"


def convex_hull_volume_A3(xyz_nm, np):
    """Convex-hull volume (A^3) of a CA point cloud given coordinates in nm.

    Raises HullDependencyUnavailable if the backend is missing (fail closed).
    Returns NaN only for genuine GEOMETRIC degeneracy (<4 points, or coplanar input),
    which is a real property of the data rather than a broken environment.
    """
    ok, why = hull_backend_available()
    if not ok:
        raise HullDependencyUnavailable(why)
    from scipy.spatial import ConvexHull
    from scipy.spatial import QhullError
    if len(xyz_nm) < 4:
        return float("nan")
    try:
        return float(ConvexHull(np.asarray(xyz_nm) * 10.0).volume)
    except QhullError:
        return float("nan")          # degenerate / coplanar region: geometry, not environment


def _dccm_matrix(prod, ca, np):
    if prod.n_frames < 2 or len(ca) < 2:
        return None
    xyz = prod.xyz[:, ca, :]
    disp = xyz - xyz.mean(axis=0, keepdims=True)
    cov = np.einsum("tix,tjx->ij", disp, disp) / max(1, prod.n_frames)
    ms = np.einsum("tix,tix->i", disp, disp) / max(1, prod.n_frames)
    denom = np.sqrt(ms[:, None] * ms[None, :])
    return np.divide(cov, denom, out=np.zeros_like(cov), where=denom > 0)


def _dccm_region_summary(dccm, ca, region_ca, np):
    if dccm is None or not region_ca:
        return {
            "internal_mean": None,
            "internal_mean_abs": None,
            "region_to_rest_mean": None,
            "region_to_rest_mean_abs": None,
        }
    pos = {atom_idx: i for i, atom_idx in enumerate(ca)}
    idx = [pos[i] for i in region_ca if i in pos]
    rest = [i for i in range(len(ca)) if i not in set(idx)]
    if not idx:
        return {
            "internal_mean": None,
            "internal_mean_abs": None,
            "region_to_rest_mean": None,
            "region_to_rest_mean_abs": None,
        }
    internal_vals = []
    if len(idx) > 1:
        block = dccm[np.ix_(idx, idx)]
        mask = ~np.eye(len(idx), dtype=bool)
        internal_vals = block[mask]
    rest_vals = dccm[np.ix_(idx, rest)].ravel() if rest else np.array([])

    def mean_or_none(values, absolute=False):
        if len(values) == 0:
            return None
        values = np.abs(values) if absolute else values
        return float(values.mean())

    return {
        "internal_mean": mean_or_none(internal_vals),
        "internal_mean_abs": mean_or_none(internal_vals, absolute=True),
        "region_to_rest_mean": mean_or_none(rest_vals),
        "region_to_rest_mean_abs": mean_or_none(rest_vals, absolute=True),
    }


def _event_summary(mask, dt_ns):
    runs = []
    start = None
    for i, val in enumerate(mask):
        if val and start is None:
            start = i
        elif not val and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(mask) - 1))
    qualifying = [(a, b) for a, b in runs if (b - a + 1) >= 2]
    durations = [(b - a + 1) * dt_ns for a, b in qualifying]
    return {
        "open_like_frame_count": int(sum(bool(x) for x in mask)),
        "open_like_fraction": float(sum(bool(x) for x in mask) / len(mask)) if len(mask) else 0.0,
        "opening_event_count_min_2_frames": len(qualifying),
        "max_opening_event_duration_ns": float(max(durations)) if durations else 0.0,
    }


def expected_frame_count_from_done(done_payload: dict) -> int:
    """Exact DCD frame count expected from the run_md.py production-step accounting."""
    timestep_fs = float(done_payload.get("timestep_fs", 4.0))
    report_ps = float(done_payload.get("report_ps", 50.0))
    production_ns = float(done_payload.get("ns", done_payload.get("production_ns", 0.0)))
    dt_ps = timestep_fs / 1000.0
    dt_ns = timestep_fs / 1_000_000.0
    prod_steps = int(round(production_ns / dt_ns))
    report_every = max(1, int(round(report_ps / dt_ps)))
    return prod_steps // report_every


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _dcd_frame_count(path: Path) -> int | None:
    try:
        from mdtraj.formats import DCDTrajectoryFile
        with DCDTrajectoryFile(str(path), "r") as fh:
            return len(fh)
    except Exception:
        return None


def validate_scientific_replicate(rep_dir: Path, expected_pdb: str | None = None,
                                  expected_role: str | None = None,
                                  expected_min_ns: float | None = None) -> dict:
    """Fail-closed completion validation for final scientific analysis."""
    issues: list[str] = []
    failed = rep_dir / "FAILED.json"
    done_path = rep_dir / "DONE.json"
    dcd = rep_dir / "production.dcd"
    provenance_path = rep_dir / "PROVENANCE.json"

    failed_payload = _read_json(failed) if failed.exists() else None
    if failed.exists():
        issues.append("FAILED.json present")
        if isinstance(failed_payload, dict) and failed_payload.get("reason"):
            issues.append(f"FAILED reason: {failed_payload['reason']}")

    done = _read_json(done_path) if done_path.exists() else None
    if not done_path.exists():
        issues.append("DONE.json missing")
    elif not isinstance(done, dict):
        issues.append("DONE.json unreadable")

    if not isinstance(done, dict):
        return {"ok": False, "issues": issues, "done": done, "expected_frames": None,
                "observed_frames": None}

    if not str(done.get("sanity_gate", "")).startswith("passed"):
        issues.append("DONE sanity_gate is not passed")
    if expected_pdb and done.get("pdb") != expected_pdb:
        issues.append(f"topology/run pdb identity mismatch: {done.get('pdb')} != {expected_pdb}")
    if expected_role and done.get("role") != expected_role:
        issues.append(f"replicate role mismatch: {done.get('role')} != {expected_role}")
    if expected_min_ns is not None and float(done.get("production_ns", 0.0)) + 1e-12 < expected_min_ns:
        issues.append(f"target duration not reached: {done.get('production_ns')} < {expected_min_ns}")
    if int(done.get("steps", 0)) < int(done.get("target_total_steps", done.get("steps", 0))):
        issues.append("target total steps not reached")

    if float(done.get("report_ps", 0.0)) <= 0.0:
        issues.append("invalid output interval report_ps")
        expected_frames = None
    else:
        expected_frames = expected_frame_count_from_done(done)

    if not dcd.exists() or dcd.stat().st_size == 0:
        issues.append("production trajectory missing or empty")
        observed_frames = None
    else:
        observed_frames = _dcd_frame_count(dcd)
        if observed_frames is None:
            observed_frames = done.get("dcd_frames")
        if expected_frames is not None and observed_frames is not None:
            if int(observed_frames) < int(expected_frames):
                issues.append(f"trajectory truncated: {observed_frames} frames < expected {expected_frames}")
            elif int(observed_frames) > int(expected_frames):
                issues.append(f"duplicate frame risk: {observed_frames} frames > expected {expected_frames}")

    done_frames = done.get("dcd_frames")
    if done_frames is not None and observed_frames is not None and int(done_frames) != int(observed_frames):
        issues.append(f"DONE dcd_frames mismatch: {done_frames} != observed {observed_frames}")

    topology_name = done.get("topology")
    if not topology_name:
        issues.append("DONE topology field missing")
    elif not (rep_dir.parent / str(topology_name)).exists():
        issues.append(f"topology file missing: {topology_name}")
    if done.get("trajectory") and done.get("trajectory") != "production.dcd":
        issues.append(f"trajectory identity mismatch: {done.get('trajectory')} != production.dcd")

    provenance = _read_json(provenance_path)
    if isinstance(provenance, dict):
        if expected_pdb and provenance.get("structure_pdb_id") != expected_pdb:
            issues.append("PROVENANCE structure_pdb_id mismatch")
        if expected_role and provenance.get("role") != expected_role:
            issues.append("PROVENANCE role mismatch")
        hashes = provenance.get("input_hashes", {})
        protocol = hashes.get("frozen_analysis_protocol_sha256")
        if not protocol:
            issues.append("protocol identity hash missing from PROVENANCE")
    else:
        issues.append("PROVENANCE.json missing or unreadable")

    times, log_status = read_log_times(rep_dir / "production.log")
    if log_status != "ok":
        # Fail closed: without the log we cannot run the duplicate-time or output-interval
        # checks, and "check not run" must never be reported as "check passed".
        issues.append(
            f"production.log unusable ({log_status}): duplicate-time and output-interval "
            "validation could not be performed"
        )
    else:
        if len(times) != len(set(times)):
            issues.append("duplicate frame/log artifacts: duplicate log times")
        if len(times) >= 2:
            # Compare each adjacent interval against the AUTHORITATIVE cadence recorded in
            # DONE.json (report_ps), with a numerical tolerance -- not against each other via
            # round()+set(). OpenMM's StateDataReporter time column is an accumulated float
            # (dt_fs * step / 1000), so two intervals that are the SAME 50 ps cadence can land
            # on different floats (e.g. 49.99999999881766 vs 50.00000001018634) purely from
            # floating-point accumulation. round(diff, 9) + set() treated those as distinct
            # cadences and rejected scientifically valid (including resumed) trajectories.
            # A real cadence discontinuity (wrong interval, dropped frame, non-monotonic time)
            # is orders of magnitude larger than this drift and still fails.
            try:
                expected_report_ps = float(done.get("report_ps"))
            except (TypeError, ValueError):
                expected_report_ps = None
            if expected_report_ps is None or expected_report_ps <= 0.0:
                issues.append(
                    "output interval could not be validated: DONE.json report_ps is "
                    "missing or invalid"
                )
            else:
                tolerance_ps = max(1e-6, abs(expected_report_ps) * 1e-9)
                diffs = [b - a for a, b in zip(times, times[1:])]
                bad = [d for d in diffs if abs(d - expected_report_ps) > tolerance_ps]
                if bad:
                    issues.append(
                        "output interval inconsistent across production.log: "
                        f"{len(bad)}/{len(diffs)} adjacent interval(s) deviate from the "
                        f"expected {expected_report_ps:g} ps cadence (DONE.json report_ps) "
                        f"by more than {tolerance_ps:g} ps, e.g. {bad[0]:.9f} ps"
                    )

    return {"ok": not issues, "issues": issues, "done": done,
            "log_status": log_status,
            "expected_frames": expected_frames, "observed_frames": observed_frames}


def assess_convergence(series, n_blocks=3, max_final_shift_sd=0.5):
    """Block-wise convergence evidence for trajectory-derived time series."""
    import numpy as _np
    x = _np.asarray(series, dtype=float)
    x = x[_np.isfinite(x)]
    if x.size < n_blocks * 2:
        return {"status": "INSUFFICIENT_DATA", "n": int(x.size), "n_blocks": int(n_blocks)}
    blocks = _np.array_split(x, n_blocks)
    means = _np.asarray([float(b.mean()) for b in blocks])
    sds = _np.asarray([float(b.std(ddof=1)) if b.size > 1 else 0.0 for b in blocks])
    pooled_sd = float(x.std(ddof=1)) if x.size > 1 else 0.0
    final_shift = float(abs(means[-1] - means[0]))
    threshold = float(max_final_shift_sd * pooled_sd)
    stable = final_shift <= threshold if pooled_sd > 0 else final_shift == 0.0
    monotonic = bool(_np.all(_np.diff(means) >= 0) or _np.all(_np.diff(means) <= 0))
    return {
        "status": "STABLE_BLOCKS" if stable else "DRIFTING_BLOCKS",
        "n": int(x.size),
        "n_blocks": int(n_blocks),
        "block_means": [float(v) for v in means],
        "block_sds": [float(v) for v in sds],
        "first_to_last_shift": final_shift,
        "pooled_sd": pooled_sd,
        "max_allowed_shift": threshold,
        "monotonic_block_means": monotonic,
    }


# Two-sided 95% Student's t critical values by degrees of freedom (df = n_replicates - 1).
# With n as small as 2-3 replicates, the normal-approximation z=1.96 badly understates the
# true interval (e.g. df=2 needs t=4.303, not 1.96) -- it silently reports a ~68% interval
# as if it were 95%. Falls back to the z=1.96 large-sample limit beyond the tabulated range.
_T95_BY_DF = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262,
    10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110,
    18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060,
    26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
}


def t95_critical_value(df: int) -> float:
    """Two-sided 95% t critical value for the given degrees of freedom (n_replicates - 1)."""
    if df < 1:
        return float("nan")
    return _T95_BY_DF.get(int(df), 1.96)


def aggregate_replicates(rows: list[dict], metric_path: tuple[str, ...] = ("openness", "open_like_fraction")) -> dict:
    """Aggregate per-replicate metrics without concatenating independent replicas."""
    import statistics

    def get(row):
        cur = row
        for key in metric_path:
            if not isinstance(cur, dict) or key not in cur:
                return None
            cur = cur[key]
        return cur

    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("role", "unknown")), []).append(row)
    out = {}
    for role, reps in grouped.items():
        vals = [float(v) for r in reps if (v := get(r)) is not None]
        mean = statistics.mean(vals) if vals else None
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0 if len(vals) == 1 else None
        ci = None
        ci_method = None
        if len(vals) >= 2:
            t_crit = t95_critical_value(len(vals) - 1)
            half = t_crit * sd / math.sqrt(len(vals))
            ci = [mean - half, mean + half]
            ci_method = f"t95(df={len(vals) - 1})={t_crit:.3f}"
        convergence = [r.get("convergence", {}).get("overall_status") for r in reps]
        out[role] = {
            "independent_unit": "replicate",
            "metric": ".".join(metric_path),
            "replicate_count": len(reps),
            "support_count": len(vals),
            "failed_or_incomplete_count": sum(1 for r in reps if r.get("completion_status") != "PASS"),
            "per_replicate": [{"replicate": r.get("replicate"), "value": get(r)} for r in reps],
            "mean": mean,
            "sd": sd,
            "approx_95ci_across_replicates": ci,
            "approx_95ci_method": ci_method,
            "range": [min(vals), max(vals)] if vals else None,
            "convergence_statuses": convergence,
        }
    return out


def kabsch_rmsd_nm(mobile, reference):
    import numpy as _np
    p = _np.asarray(mobile, dtype=float)
    q = _np.asarray(reference, dtype=float)
    pc = p - p.mean(axis=0)
    qc = q - q.mean(axis=0)
    h = pc.T @ qc
    u, _s, vt = _np.linalg.svd(h)
    d = 1.0 if _np.linalg.det(vt.T @ u.T) >= 0.0 else -1.0
    rot = vt.T @ _np.diag([1.0, 1.0, d]) @ u.T
    diff = (pc @ rot.T) - qc
    return float(_np.sqrt((diff * diff).sum(axis=1).mean()))


# --------------------------------------------------------------------------------------
# Dynamic discriminators (trajectory_dynamic_control_gate_v2)
#
# WHY THIS EXISTS.  Gate v1 accepted three STATIC 8GLA structures plus ~0.10 A of independent
# per-frame coordinate jitter as a passing positive control.  Reproduced 2026-08-16:
#   * 8GLA's frozen static reference already sits ABOVE both midpoint openness thresholds
#     (SASA 839.1 >= 808.6 A^2; CA hull 610.3 >= 560.7 A^3), so a static 8GLA run scores
#     open_like_fraction = 1.0 from frame zero without moving at all; and
#   * IID jitter of 0.10 A/axis yields RMSF 0.0174 nm, which clears the 0.015 nm floor.
# The only dynamic discriminator was that absolute RMSF floor, and white noise clears it.
# That contradicts the frozen protocol's own negative_diagnostic, which requires exactly this
# case to FAIL.
#
# THE FIX.  Add two predeclared discriminators whose null distribution under independent
# per-frame noise is ANALYTIC, so the thresholds are derived from the noise null and NOT from
# any MD outcome.  Both are collective backbone observables:
#
#   D1  temporal structure: lag-1 autocorrelation r1 of the supported-region CA convex-hull
#       volume series.  Under an IID null, r1 has mean ~ -1/N and SD ~ 1/sqrt(N), so a
#       threshold of K_SIGMA/sqrt(N) is a K_SIGMA one-sided rejection of "independent frames".
#       Real MD hull volume is a slow collective coordinate and is strongly autocorrelated at
#       the frozen 50 ps cadence; IID jitter has r1 ~ 0.
#
#   D2  spatial collectivity: mean |DCCM| among supported-region CA atoms.  Under an IID null
#       each off-diagonal correlation is ~N(0, 1/sqrt(N)), so E[|c|] = sqrt(2/pi)/sqrt(N).
#       A threshold of K_SIGMA x that null mean requires genuinely collective displacement.
#       Real MD gives 0.3-0.7 for a contiguous region; IID jitter sits at the null floor.
#
# Both thresholds scale with N automatically, so they cannot be tuned by choosing a run
# length, and neither was selected by inspecting any control5 result -- none exists yet.
# --------------------------------------------------------------------------------------
DYNAMIC_NULL_K_SIGMA = 3.0          # one-sided rejection strength against the IID-noise null
_HALF_NORMAL_MEAN = math.sqrt(2.0 / math.pi)   # E[|z|] for z ~ N(0,1)


def lag1_autocorrelation(series) -> float | None:
    """Lag-1 Pearson autocorrelation of a 1-D series; None if undefined (constant/too short)."""
    import numpy as _np
    x = _np.asarray(series, dtype=float)
    x = x[_np.isfinite(x)]
    if x.size < 3:
        return None
    x = x - x.mean()
    denom = float((x * x).sum())
    if denom <= 0.0:
        return None
    return float((x[:-1] * x[1:]).sum() / denom)


def autocorrelation_null_threshold(n_frames: int, k_sigma: float = DYNAMIC_NULL_K_SIGMA) -> float | None:
    """K-sigma one-sided rejection of the IID null for a lag-1 autocorrelation."""
    if not n_frames or n_frames < 3:
        return None
    return float(k_sigma / math.sqrt(float(n_frames)))


def dccm_null_threshold(n_frames: int, k_sigma: float = DYNAMIC_NULL_K_SIGMA) -> float | None:
    """K x the analytic IID-null expectation of mean |DCCM| for N independent frames."""
    if not n_frames or n_frames < 3:
        return None
    return float(k_sigma * _HALF_NORMAL_MEAN / math.sqrt(float(n_frames)))


def static_noise_surrogate_stats(region_xyz_nm, rmsf_nm: float, n_frames: int, seed: int = 20260816):
    """Matched static + IID-noise surrogate for the SAME region, as a reported null reference.

    Takes the region's frame-0 CA coordinates, adds independent per-frame Gaussian noise
    scaled to reproduce the observed RMSF, and returns the same D1/D2 statistics. This is
    diagnostic context for the reviewer -- the gate itself uses the analytic nulls above --
    but it makes the "is this trajectory distinguishable from a jittered crystal structure?"
    comparison explicit in the output rather than implicit in a threshold.
    """
    import numpy as _np
    ref = _np.asarray(region_xyz_nm, dtype=float)
    if ref.ndim != 2 or ref.shape[0] < 4 or n_frames < 3:
        return None
    sigma = float(rmsf_nm) / math.sqrt(3.0) if rmsf_nm and rmsf_nm > 0 else 0.0
    rng = _np.random.default_rng(seed)
    xyz = ref[None, :, :] + rng.normal(0.0, sigma, size=(int(n_frames),) + ref.shape)
    try:
        hull = _np.array([convex_hull_volume_A3(frame, _np) for frame in xyz])
        hull_r1 = lag1_autocorrelation(hull)
    except HullDependencyUnavailable:
        hull_r1 = None
    disp = xyz - xyz.mean(axis=0, keepdims=True)
    cov = _np.einsum("tix,tjx->ij", disp, disp) / max(1, int(n_frames))
    ms = _np.einsum("tix,tix->i", disp, disp) / max(1, int(n_frames))
    denom = _np.sqrt(ms[:, None] * ms[None, :])
    dccm = _np.divide(cov, denom, out=_np.zeros_like(cov), where=denom > 0)
    mask = ~_np.eye(dccm.shape[0], dtype=bool)
    return {
        "description": "frame-0 region CA + IID Gaussian noise matched to the observed RMSF",
        "n_frames": int(n_frames),
        "per_axis_sigma_nm": sigma,
        "hull_volume_lag1_autocorrelation": hull_r1,
        "region_internal_mean_abs_dccm": float(_np.abs(dccm[mask]).mean()) if mask.any() else None,
    }


def evaluate_control_interpretability(rows, min_replicates=CONTROL_MIN_REPLICATES):
    """Trajectory-derived positive-control criterion (trajectory_dynamic_control_gate_v2).

    Deliberately ignores frame-zero / static apo-control separation. A control replicate
    qualifies only if it is complete, artifact-free, open-like under the frozen thresholds,
    AND statistically distinguishable from a static structure with independent per-frame
    coordinate noise on both a temporal (D1) and a collectivity (D2) discriminator.
    """
    control = [r for r in rows if r.get("role") == "control"]
    issues = []
    if len(control) < min_replicates:
        issues.append(f"control replicates {len(control)} < {min_replicates}")

    qualifying = 0
    per_replicate = []
    for r in control:
        rep = f"{r.get('pdb', 'control')}/{r.get('replicate', '?')}"
        rep_issues = []
        ns = float(r.get("n_frames", 0)) * float(r.get("dt_ns", 0.0))
        if ns + 1e-9 < CONTROL_MIN_NS:
            rep_issues.append(f"analyzed trajectory length {ns:.3f} ns < {CONTROL_MIN_NS:.1f} ns")
        if r.get("pbc_artifact_suspected"):
            rep_issues.append("PBC artifact suspected")
        if r.get("duplicate_log_times") or r.get("frame_count_status") == "too_many_frames_duplicate_risk":
            rep_issues.append("duplicate-frame risk")
        if r.get("completion_status") not in (None, "PASS"):
            rep_issues.append(f"completion status {r.get('completion_status')}")

        openness = r.get("openness") or {}
        if not openness.get("available"):
            rep_issues.append(f"openness unavailable: {openness.get('reason', 'no reason recorded')}")
        open_frac = float(openness.get("open_like_fraction") or 0.0)
        if open_frac < CONTROL_MIN_OPEN_LIKE_FRACTION:
            rep_issues.append(
                f"open-like fraction {open_frac:.3f} below {CONTROL_MIN_OPEN_LIKE_FRACTION:.3f}")

        rmsf = float(r.get("pocket_rmsf_mean_nm") or 0.0)
        if rmsf < CONTROL_MIN_RMSF_NM:
            rep_issues.append(
                f"pocket RMSF {rmsf:.4f} nm below dynamic floor {CONTROL_MIN_RMSF_NM:.4f} nm")

        # --- D1 / D2: reject the "static structure + per-frame noise" null -----------------
        dyn = r.get("dynamics") or {}
        n_prod = int(dyn.get("n_production_frames") or 0)
        r1 = dyn.get("hull_volume_lag1_autocorrelation")
        dccm_abs = dyn.get("region_internal_mean_abs_dccm")
        r1_thr = autocorrelation_null_threshold(n_prod)
        dccm_thr = dccm_null_threshold(n_prod)

        if r1_thr is None or dccm_thr is None:
            rep_issues.append(
                f"dynamic discriminators unavailable: only {n_prod} production frames")
        else:
            if r1 is None:
                rep_issues.append(
                    "D1 hull-volume lag-1 autocorrelation unavailable "
                    f"({dyn.get('hull_unavailable_reason', 'no reason recorded')})")
            elif float(r1) < r1_thr:
                rep_issues.append(
                    f"D1 hull-volume lag-1 autocorrelation {float(r1):.4f} < IID-null "
                    f"rejection threshold {r1_thr:.4f} (N={n_prod}): indistinguishable from "
                    "independent per-frame noise")
            if dccm_abs is None:
                rep_issues.append("D2 region-internal mean |DCCM| unavailable")
            elif float(dccm_abs) < dccm_thr:
                rep_issues.append(
                    f"D2 region-internal mean |DCCM| {float(dccm_abs):.4f} < IID-null "
                    f"rejection threshold {dccm_thr:.4f} (N={n_prod}): displacement is not "
                    "collective")

        dynamics_detected = (
            r1_thr is not None and dccm_thr is not None
            and r1 is not None and dccm_abs is not None
            and float(r1) >= r1_thr and float(dccm_abs) >= dccm_thr
        )
        per_replicate.append({
            "replicate": rep,
            "qualifies": not rep_issues,
            "dynamics_detected": dynamics_detected,
            "open_like_fraction": open_frac,
            "pocket_rmsf_mean_nm": rmsf,
            "n_production_frames": n_prod,
            "D1_hull_lag1_autocorrelation": r1,
            "D1_iid_null_threshold": r1_thr,
            "D2_region_internal_mean_abs_dccm": dccm_abs,
            "D2_iid_null_threshold": dccm_thr,
            "static_noise_surrogate": dyn.get("static_noise_surrogate"),
            "issues": rep_issues,
        })
        if not rep_issues:
            qualifying += 1
        issues.extend(f"{rep}: {x}" for x in rep_issues)

    pass_gate = len(control) >= min_replicates and qualifying >= min_replicates and not issues
    n_dynamic = sum(1 for pr in per_replicate if pr["dynamics_detected"])
    if pass_gate:
        reason = (
            "PASS: independent control trajectories are complete, artifact-free, open-like, and "
            "their motion is statistically distinguishable from a static structure with "
            "per-frame coordinate noise on both the temporal and collectivity discriminators."
        )
    elif n_dynamic == 0:
        # No replicate rejected the static-structure-plus-noise null: this really is a "the
        # trajectories look like jittered crystal structures" failure.
        reason = (
            "FAIL: control trajectories did not demonstrate trajectory-derived dynamics beyond "
            "static starting-state separation plus per-frame noise."
        )
    else:
        # At least one replicate rejected the IID-noise null (D1 and D2 both cleared their
        # analytic thresholds), so the blanket "no dynamics" message would misstate the result.
        # The gate still failed for some other, separately-named reason (most commonly the
        # frozen open-like-fraction reproducibility floor) -- name that reason instead of
        # implying the trajectories were indistinguishable from noise.
        reason = (
            f"FAIL: {n_dynamic}/{len(control)} control replicate(s) demonstrated trajectory-"
            "derived dynamics distinguishable from a static structure plus per-frame noise "
            f"(D1 and D2 both cleared their analytic IID-null thresholds), but only "
            f"{qualifying}/{len(control)} replicate(s) met every frozen qualification criterion. "
            f"The gate requires {int(min_replicates)}/{int(min_replicates)}. "
            f"Per-replicate detail: {'; '.join(issues) if issues else 'see per_replicate'}."
        )
    return {
        "name": "trajectory_dynamic_control_gate_v2",
        "status": "PASS" if pass_gate else "FAIL",
        "interpretable": bool(pass_gate),
        "criterion_frozen_before_meaningful_control_md": True,
        "uses_frame_zero_or_static_apo_control_difference": False,
        "rejects_static_structure_plus_per_frame_noise": True,
        "minimum_control_replicates": int(min_replicates),
        "minimum_control_ns_per_replicate": CONTROL_MIN_NS,
        "minimum_pocket_rmsf_nm": CONTROL_MIN_RMSF_NM,
        "minimum_open_like_fraction": CONTROL_MIN_OPEN_LIKE_FRACTION,
        "dynamic_discriminators": {
            "D1": "lag-1 autocorrelation of supported-region CA convex-hull volume "
                  f">= {DYNAMIC_NULL_K_SIGMA}/sqrt(N_production_frames)",
            "D2": "supported-region internal mean |DCCM| >= "
                  f"{DYNAMIC_NULL_K_SIGMA} * sqrt(2/pi)/sqrt(N_production_frames)",
            "null_model": "independent per-frame coordinate noise about a static structure",
            "thresholds_derived_from": "analytic IID null distribution, not from any MD outcome",
            "k_sigma": DYNAMIC_NULL_K_SIGMA,
        },
        "qualifying_control_replicates": int(qualifying),
        "replicates_with_detected_dynamics": int(n_dynamic),
        "per_replicate": per_replicate,
        "issues": issues,
        "reason": reason,
    }


def estimate_analysis_ram_bytes(n_atoms: int, n_frames: int, working_copies: int = 4) -> dict:
    """Approximate peak RAM for the streaming analysis path (float32 xyz + working copies)."""
    per_frame = int(n_atoms) * 3 * 4
    base = per_frame * int(n_frames)
    return {
        "atoms_loaded": int(n_atoms),
        "frames_loaded": int(n_frames),
        "bytes_per_frame": per_frame,
        "coordinate_bytes": int(base),
        "assumed_working_copies": int(working_copies),
        "estimated_peak_bytes": int(base * working_copies),
        "estimated_peak_gib": round(base * working_copies / (1024 ** 3), 3),
    }


def analyze_replicate(dcd: Path, top_pdb: Path, resseqs, interface_chain_indices,
                      ns_per_frame_hint=0.05, allow_keys=None, regions=None,
                      thresholds=None, done_payload=None, stride=1,
                      primary_region_name="supported_ge2of3"):
    md, np, pd, _ = _imports()
    # --- memory safety: never load solvent -------------------------------------------------
    # A 100 ns replicate of the solvated PCNA homotrimer is ~2000 frames x ~100k atoms. Loading
    # the whole box costs ~2.4 GB of coordinates per replicate before any working copy, and
    # every metric below operates on the PROTEIN slice anyway. Selecting protein atoms AT READ
    # TIME (rather than loading everything and slicing) drops that by roughly an order of
    # magnitude. This does not change the trajectory sampling frequency; --stride is separate,
    # off by default, and recorded in the output when used.
    ref = md.load(str(top_pdb))
    protein_idx = ref.top.select("protein")
    if protein_idx is None or len(protein_idx) == 0:
        sys.exit(f"[analyze] FATAL: topology {top_pdb} contains no protein atoms.")
    stride = max(1, int(stride))
    traj = md.load(str(dcd), top=str(top_pdb), atom_indices=protein_idx, stride=stride)
    ram_estimate = estimate_analysis_ram_bytes(len(protein_idx), traj.n_frames)
    del ref
    # 1) PBC fix BEFORE anything else
    try:
        traj.image_molecules(inplace=True)
    except Exception:
        traj.make_molecules_whole(inplace=True)
    protein = traj
    ca = protein.top.select("name CA")
    pocket_atoms = pocket_selection(protein.top, resseqs, interface_chain_indices,
                                    allow_keys=allow_keys)
    if not pocket_atoms:
        sys.exit(f"[analyze] FATAL: empty pocket selection for {dcd} — "
                 f"resseqs={sorted(set(resseqs))[:8]}... chains={interface_chain_indices}. "
                 f"An empty selection must fail loudly, not silently produce NaN metrics.")
    pocket_ca = [i for i in pocket_atoms if protein.top.atom(i).name == "CA"]
    # 2) align on core Ca that EXCLUDES the pocket (no circularity)
    pocket_ca_set = set(pocket_ca)
    core = np.array([i for i in ca if i not in pocket_ca_set])
    protein.superpose(protein, frame=0, atom_indices=core, ref_atom_indices=core)
    # frames -> ns: read the ACTUAL save interval from the run manifest/log (not hardcoded)
    dt_ns, dt_src = _frame_interval_ns(dcd.parent, np, ns_per_frame_hint)
    n = protein.n_frames
    equil = int(EQUIL_NS / dt_ns)
    if n > equil:
        prod = protein[equil:]; equil_used = equil
    else:
        print(f"[warn] {dcd.parent.name}: only {n} frames (~{n*dt_ns:.1f} ns @ "
              f"{dt_ns:.4f} ns/frame, src={dt_src}) <= equilibration cutoff {equil} frames "
              f"({EQUIL_NS} ns) -> equilibration NOT discarded for this replicate.")
        prod = protein; equil_used = 0
    # 3) backbone RMSD (sanity) + pocket RMSF about the mean
    rmsd = md.rmsd(protein, protein, 0, atom_indices=core)  # nm
    rmsd_prod = rmsd[equil_used:]
    if rmsd_prod.size == 0:
        rmsd_prod = rmsd
    # --- PBC artifact = a discontinuous single-frame jump; real motion is smooth (audit fix) ---
    frame_jumps = np.abs(np.diff(rmsd)) if rmsd.size > 1 else np.array([0.0])
    max_jump_nm = float(frame_jumps.max()) if frame_jumps.size else 0.0
    pbc_artifact_suspected = bool(max_jump_nm > PBC_JUMP_NM)
    large_smooth_drift = bool(rmsd.max() > DRIFT_INFO_NM and not pbc_artifact_suspected)
    mean_xyz = prod.xyz[:, pocket_ca, :].mean(axis=0)
    rmsf = np.sqrt(((prod.xyz[:, pocket_ca, :] - mean_xyz) ** 2).sum(axis=2).mean(axis=0))  # nm
    # 4) pocket openness proxies, PER CHAIN then averaged (never summed across chains)
    sasa_res = md.shrake_rupley(prod, mode="residue")  # nm^2 per residue
    dccm = _dccm_matrix(prod, ca, np)

    def region_series(region_atoms, region_ca):
        res_by_chain = {}
        for atom_i in region_atoms:
            res = protein.top.atom(atom_i).residue
            res_by_chain.setdefault(res.chain.index, set()).add(res.index)
        per_chain = []
        for cidx in sorted(res_by_chain):
            per_chain.append(sasa_res[:, sorted(res_by_chain[cidx])].sum(axis=1))
        per_chain = np.array(per_chain)
        sasa_nm2 = per_chain.mean(axis=0) if len(per_chain) else np.array([])
        rg_list = []
        for cidx in sorted(res_by_chain):
            ca_this = [i for i in region_ca if protein.top.atom(i).residue.chain.index == cidx]
            if ca_this:
                rg_list.append(md.compute_rg(prod.atom_slice(ca_this)))
        rg = (np.mean(np.array(rg_list), axis=0) if rg_list
              else (md.compute_rg(prod.atom_slice(region_ca)) if region_ca else np.array([])))
        hull_reason = None
        if region_ca:
            region_mean = prod.xyz[:, region_ca, :].mean(axis=0)
            region_rmsf = np.sqrt(((prod.xyz[:, region_ca, :] - region_mean) ** 2).sum(axis=2).mean(axis=0))
            try:
                hull = np.array([convex_hull_volume_A3(frame_xyz, np)
                                 for frame_xyz in prod.xyz[:, region_ca, :]])
            except HullDependencyUnavailable as exc:
                hull = np.array([])
                hull_reason = str(exc)
            # --- region RMSD, two DISTINCT and separately labelled quantities --------------
            # `protein` was superposed onto frame 0 using the scaffold CA set, so the frames
            # already carry the scaffold transformation. Measuring the region directly against
            # frame 0 on those coordinates is region RMSD AFTER SCAFFOLD ALIGNMENT: it retains
            # the region's displacement RELATIVE to the scaffold.
            #
            # md.rmsd(..., atom_indices=region_ca) does NOT do that -- it re-superposes on the
            # region itself, which discards exactly that relative displacement. Before the
            # 2026-08-16 repair the production path used md.rmsd here while the emitted
            # metadata claimed "region CA after scaffold alignment", so a region rigidly
            # displaced 0.5 nm against a fixed scaffold was reported as 0.000 nm.
            reg_xyz = protein.xyz[:, region_ca, :]
            d = reg_xyz - reg_xyz[0]
            scaffold_aligned = np.sqrt((d * d).sum(axis=2).mean(axis=1))
            local_rmsd = scaffold_aligned[equil_used:]
            if local_rmsd.size == 0:
                local_rmsd = scaffold_aligned
            internal_rmsd_all = md.rmsd(protein, protein, 0, atom_indices=region_ca)
            internal_rmsd = internal_rmsd_all[equil_used:]
            if internal_rmsd.size == 0:
                internal_rmsd = internal_rmsd_all
        else:
            region_rmsf = np.array([])
            hull = np.array([])
            local_rmsd = np.array([])
            internal_rmsd = np.array([])
        convergence = {}
        if len(sasa_nm2):
            convergence["sasa_A2"] = assess_convergence(sasa_nm2 * 100.0)
        if len(hull):
            convergence["ca_convex_hull_volume_A3"] = assess_convergence(hull)
        if len(local_rmsd):
            convergence["region_rmsd_scaffold_aligned_nm"] = assess_convergence(local_rmsd)
        overall_status = "INSUFFICIENT_DATA"
        if convergence:
            statuses = [v.get("status") for v in convergence.values()]
            overall_status = "DRIFTING_BLOCKS" if "DRIFTING_BLOCKS" in statuses else (
                "STABLE_BLOCKS" if "STABLE_BLOCKS" in statuses else "INSUFFICIENT_DATA"
            )
        return (res_by_chain, sasa_nm2, rg, region_rmsf, hull, local_rmsd, internal_rmsd,
                hull_reason, convergence, overall_status)

    regions = regions or {"pocket": list(resseqs)}
    region_metrics = {}
    region_ca_by_name = {}
    for region_name, region_resseqs in regions.items():
        region_atoms = pocket_selection(protein.top, region_resseqs, interface_chain_indices,
                                        allow_keys=allow_keys)
        region_ca = [i for i in region_atoms if protein.top.atom(i).name == "CA"]
        region_ca_by_name[region_name] = region_ca
        (res_by_chain, sasa_nm2, rg, region_rmsf, hull_A3, local_rmsd, internal_rmsd,
         hull_reason, convergence, overall_status) = region_series(region_atoms, region_ca)
        available = bool(len(region_atoms) and len(region_ca) and len(sasa_nm2))
        region_metrics[region_name] = {
            "available": available,
            "n_atoms": int(len(region_atoms)),
            "n_ca": int(len(region_ca)),
            "n_chains": int(len(res_by_chain)),
            "sasa_mean_A2": float(sasa_nm2.mean() * 100.0) if len(sasa_nm2) else None,
            "sasa_std_A2": float(sasa_nm2.std() * 100.0) if len(sasa_nm2) else None,
            "sasa_max_A2": float(sasa_nm2.max() * 100.0) if len(sasa_nm2) else None,
            "rmsf_mean_nm": float(region_rmsf.mean()) if len(region_rmsf) else None,
            "rmsf_max_nm": float(region_rmsf.max()) if len(region_rmsf) else None,
            # Region displacement RELATIVE to the scaffold (scaffold transform preserved).
            "region_rmsd_scaffold_aligned_mean_nm": float(local_rmsd.mean()) if len(local_rmsd) else None,
            "region_rmsd_scaffold_aligned_max_nm": float(local_rmsd.max()) if len(local_rmsd) else None,
            # Region-internal deformation only (region re-superposed on itself).
            "region_internal_rmsd_mean_nm": float(internal_rmsd.mean()) if len(internal_rmsd) else None,
            "region_internal_rmsd_max_nm": float(internal_rmsd.max()) if len(internal_rmsd) else None,
            "rg_mean_nm": float(rg.mean()) if len(rg) else None,
            "rg_max_nm": float(rg.max()) if len(rg) else None,
            "ca_convex_hull_volume_available": bool(len(hull_A3) and not np.isnan(hull_A3).all()),
            "ca_convex_hull_unavailable_reason": hull_reason or (
                "all frames geometrically degenerate"
                if len(hull_A3) and np.isnan(hull_A3).all() else None
            ),
            "ca_convex_hull_volume_mean_A3": (
                float(np.nanmean(hull_A3)) if len(hull_A3) and not np.isnan(hull_A3).all() else None
            ),
            "ca_convex_hull_volume_max_A3": (
                float(np.nanmax(hull_A3)) if len(hull_A3) and not np.isnan(hull_A3).all() else None
            ),
            "dccm": _dccm_region_summary(dccm, ca, region_ca, np),
            "convergence": convergence | {"overall_status": overall_status},
        }
        if len(sasa_nm2):
            region_metrics[region_name]["_sasa_series_A2"] = (sasa_nm2 * 100.0).tolist()
        if len(hull_A3):
            region_metrics[region_name]["_hull_series_A3"] = hull_A3.tolist()

    pocket_res_by_chain, pocket_sasa, rg_pocket, *_ = region_series(pocket_atoms, pocket_ca)
    thresholds = thresholds or {}
    primary = region_metrics.get(primary_region_name)

    # ---- openness: every input must be genuinely present, or the metric is UNAVAILABLE ----
    # Fail closed. A NaN hull series (missing scipy) previously produced available=True with
    # open_like_fraction=0.0, i.e. an environment defect masquerading as the scientific result
    # "the pocket never opened".
    hull_ok, hull_why = hull_backend_available()
    if primary is None:
        openness = {"available": False,
                    "reason": f"primary region {primary_region_name!r} not present in this topology"}
    elif not hull_ok:
        openness = {"available": False, "reason": f"convex-hull backend unavailable: {hull_why}"}
    elif "_sasa_series_A2" not in primary:
        openness = {"available": False, "reason": "region SASA series unavailable"}
    elif "_hull_series_A3" not in primary or not primary.get("ca_convex_hull_volume_available"):
        openness = {"available": False,
                    "reason": "region CA convex-hull volume series unavailable: "
                              f"{primary.get('ca_convex_hull_unavailable_reason') or 'unknown'}"}
    else:
        sasa_thr = thresholds.get("supported_sasa_A2")
        hull_thr = thresholds.get("supported_ca_convex_hull_volume_A3")
        if sasa_thr is None or hull_thr is None:
            openness = {"available": False,
                        "reason": "frozen openness thresholds missing from "
                                  "FROZEN_MD_ANALYSIS_PROTOCOL.json"}
        else:
            s = np.asarray(primary["_sasa_series_A2"], dtype=float)
            h = np.asarray(primary["_hull_series_A3"], dtype=float)
            if not np.isfinite(s).all() or not np.isfinite(h).all():
                openness = {"available": False,
                            "reason": "non-finite values in the region SASA or hull series"}
            else:
                mask = (s >= float(sasa_thr)) & (h >= float(hull_thr))
                openness = {
                    "available": True,
                    "thresholds": {
                        "supported_sasa_A2": float(sasa_thr),
                        "supported_ca_convex_hull_volume_A3": float(hull_thr),
                    },
                    **_event_summary(mask, dt_ns),
                }

    # ---- D1/D2 dynamic discriminators on the primary region (see gate v2 rationale) -------
    primary_ca = region_ca_by_name.get(primary_region_name) or []
    dynamics = {
        "primary_region": primary_region_name,
        "n_production_frames": int(prod.n_frames),
        "hull_volume_lag1_autocorrelation": None,
        "hull_unavailable_reason": None,
        "region_internal_mean_abs_dccm": None,
        "static_noise_surrogate": None,
    }
    if primary is not None and "_hull_series_A3" in primary and primary.get("ca_convex_hull_volume_available"):
        dynamics["hull_volume_lag1_autocorrelation"] = lag1_autocorrelation(primary["_hull_series_A3"])
    else:
        dynamics["hull_unavailable_reason"] = (
            hull_why if not hull_ok
            else ((primary or {}).get("ca_convex_hull_unavailable_reason") or "region unavailable")
        )
    if primary is not None:
        dynamics["region_internal_mean_abs_dccm"] = (
            (primary.get("dccm") or {}).get("internal_mean_abs")
        )
    if primary_ca and prod.n_frames >= 3:
        try:
            dynamics["static_noise_surrogate"] = static_noise_surrogate_stats(
                prod.xyz[0, primary_ca, :],
                float((primary or {}).get("rmsf_mean_nm") or 0.0),
                int(prod.n_frames),
            )
        except Exception as exc:            # a diagnostic must never break the analysis
            dynamics["static_noise_surrogate"] = {"error": f"{type(exc).__name__}: {exc}"}

    for metric in region_metrics.values():
        metric.pop("_sasa_series_A2", None)
        metric.pop("_hull_series_A3", None)
    times, log_status = read_log_times(dcd.parent / "production.log")
    duplicate_log_times = bool(times and len(times) != len(set(times)))
    expected_frames = None
    frame_count_status = "unchecked"
    if done_payload:
        try:
            expected_frames = expected_frame_count_from_done(done_payload)
            if n > expected_frames:
                frame_count_status = "too_many_frames_duplicate_risk"
            elif n < expected_frames:
                frame_count_status = "fewer_frames_than_regular_cadence"
            else:
                frame_count_status = "ok"
        except Exception:
            frame_count_status = "could_not_evaluate"
    return {
        "n_frames": int(n), "equil_frames": int(equil_used),
        "dt_ns": float(dt_ns), "dt_source": dt_src,
        "equil_ns_actual": float(equil_used * dt_ns),
        "n_pocket_chains": int(len(pocket_res_by_chain)),
        "rmsd_mean_nm": float(rmsd_prod.mean()), "rmsd_max_nm": float(rmsd.max()),
        "max_frame_jump_nm": max_jump_nm,
        "pbc_artifact_suspected": pbc_artifact_suspected,
        "large_smooth_drift": large_smooth_drift,
        "pocket_rmsf_mean_nm": float(rmsf.mean()), "pocket_rmsf_max_nm": float(rmsf.max()),
        "pocket_sasa_mean_nm2": float(pocket_sasa.mean()), "pocket_sasa_std_nm2": float(pocket_sasa.std()),
        "pocket_sasa_max_nm2": float(pocket_sasa.max()),
        "pocket_rg_mean_nm": float(rg_pocket.mean()), "pocket_rg_max_nm": float(rg_pocket.max()),
        "regions": region_metrics,
        "openness": openness,
        "dynamics": dynamics,
        "expected_frames_from_done": expected_frames,
        "frame_count_status": frame_count_status,
        "duplicate_log_times": duplicate_log_times,
        "production_log_status": log_status,
        "analysis_stride": int(stride),
        "ram_estimate": ram_estimate,
        "_sasa_series": pocket_sasa.tolist(),
    }


def read_log_times(log_path: Path) -> tuple[list[float], str]:
    """Parse the StateDataReporter time column, reporting WHY it failed when it does.

    Returns ``(times, status)`` where status is one of ``ok``, ``missing``, ``unreadable``,
    ``empty``, ``no_time_column``, ``no_time_rows``. Duplicate-time and output-interval
    validation depend on this; before the 2026-08-16 repair every failure mode collapsed to
    ``[]``, which silently DISABLED both checks instead of failing closed.
    """
    if not log_path.exists():
        return [], "missing"
    try:
        raw = log_path.read_text()
    except Exception:
        return [], "unreadable"
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        return [], "empty"
    header = lines[0].lstrip("#").split("\t")
    tcol = next((i for i, h in enumerate(header) if "Time (ps)" in h), None)
    if tcol is None:
        return [], "no_time_column"
    times = []
    for ln in lines[1:]:
        parts = ln.split("\t")
        if len(parts) > tcol:
            try:
                times.append(float(parts[tcol]))
            except ValueError:
                pass
    return times, ("ok" if times else "no_time_rows")


def _parse_log_times(log_path: Path):
    """Backwards-compatible times-only accessor. Prefer read_log_times for validation."""
    return read_log_times(log_path)[0]


def _frame_interval_ns(rep_dir: Path, np, hint: float):
    done = rep_dir / "DONE.json"
    if done.exists():
        try:
            rp = json.loads(done.read_text()).get("report_ps")
            if rp:
                return float(rp) / 1000.0, "DONE.json:report_ps"
        except Exception:
            pass
    times = _parse_log_times(rep_dir / "production.log")
    if len(times) >= 2:
        d = float(np.median(np.diff(np.asarray(times[:12]))))
        if d > 0:
            return d / 1000.0, "production.log:time-column"
    return float(hint), "hint(fallback)"


def _analysis_done_status(rep_dir: Path):
    done = rep_dir / "DONE.json"
    if not done.exists():
        return False, "DONE.json missing", None
    try:
        payload = json.loads(done.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"DONE.json unreadable: {exc}", None
    if not str(payload.get("sanity_gate", "")).startswith("passed"):
        return False, "DONE sanity gate did not pass", payload
    if float(payload.get("production_ns", 0.0)) <= 0.0:
        return False, "DONE production_ns is zero", payload
    if int(payload.get("steps", 0)) < int(payload.get("target_total_steps", payload.get("steps", 0))):
        return False, "DONE steps are below target_total_steps", payload
    return True, "complete", payload


def _protocol_thresholds():
    protocol = HERE / "FROZEN_MD_ANALYSIS_PROTOCOL.json"
    try:
        data = json.loads(protocol.read_text(encoding="utf-8"))
        return data.get("metrics", {}).get("openness", {}).get("thresholds", {})
    except Exception:
        return {}


def sha256_file(path: Path) -> str | None:
    """SHA-256 of a file, streamed. None when the file is absent."""
    import hashlib
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*a) -> str | None:
    import subprocess
    try:
        return subprocess.check_output(["git", "-C", str(HERE.parent), *a], text=True,
                                       stderr=subprocess.DEVNULL, timeout=10).strip() or None
    except Exception:
        return None


def analysis_provenance(out: Path, args, rows: list[dict]) -> dict:
    """Everything needed to trace these derived results back to cloud-resident raw inputs.

    The DCD files stay on the cloud instance. This block records their SHA-256 so a compact
    bundle of JSON/CSV/PNG remains verifiably tied to the exact trajectories it came from.
    """
    import platform as _plat
    import sys as _sys
    inputs = []
    for r in rows:
        rep_dir = out / str(r.get("pdb")) / str(r.get("replicate"))
        inputs.append({
            "role": r.get("role"),
            "pdb": r.get("pdb"),
            "replicate": r.get("replicate"),
            "production_dcd": str(rep_dir / "production.dcd"),
            "production_dcd_sha256": sha256_file(rep_dir / "production.dcd"),
            "production_dcd_bytes": (rep_dir / "production.dcd").stat().st_size
            if (rep_dir / "production.dcd").exists() else None,
            "system_solvated_pdb_sha256": sha256_file(rep_dir.parent / "system_solvated.pdb"),
            "done_json_sha256": sha256_file(rep_dir / "DONE.json"),
            "provenance_json_sha256": sha256_file(rep_dir / "PROVENANCE.json"),
            "production_log_sha256": sha256_file(rep_dir / "production.log"),
            "equilibration_log_sha256": sha256_file(rep_dir / "equilibration.log"),
        })
    try:
        import mdtraj as _mdt
        mdtraj_version = _mdt.version.version
    except Exception:
        mdtraj_version = None
    return {
        "generated_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
        "analysis_code_sha256": sha256_file(Path(__file__).resolve()),
        "analysis_protocol_sha256": sha256_file(HERE / "FROZEN_MD_ANALYSIS_PROTOCOL.json"),
        "pocket_definition_sha256": sha256_file(HERE / "pockets" / f"{args.pocket}.json"),
        "static_reference_sha256": sha256_file(HERE / "static_reference_analysis.json"),
        "git_commit": _git("rev-parse", "HEAD"),
        "git_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "git_dirty": bool(_git("status", "--short")),
        "command": " ".join(_sys.argv),
        "stride": int(args.stride),
        "host": {"platform": _plat.platform(), "python": _sys.version.split()[0],
                 "mdtraj": mdtraj_version},
        "raw_inputs_remain_on_this_filesystem": True,
        "raw_inputs": inputs,
    }


def _prep_caveat(out: Path, pdb: str):
    """Surface resolution / rebuilt-residue caveats from prep_audit.json (audit medium finding)."""
    ap = out / pdb / "prep" / "prep_audit.json"
    if not ap.exists():
        return None
    try:
        a = json.loads(ap.read_text())
        return {"pdb": pdb, "assembly": a.get("assembly"),
                "internal_residues_rebuilt": a.get("internal_missing_residues_rebuilt"),
                "final_chains": a.get("final_chains")}
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description="PCNA MD validation analysis (v2).")
    ap.add_argument("--pocket", default="final_consensus_1w60_20260815")
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--allow-incomplete-diagnostic", action="store_true",
                    help="analyze incomplete DCDs for debugging only; outputs are marked "
                         "DIAGNOSTIC_ONLY / NOT_FOR_SCIENTIFIC_INTERPRETATION")
    ap.add_argument("--allow-incomplete", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--keep-termini", action="store_true",
                    help="do NOT drop terminus/gap-adjacent pocket residues (their SASA "
                         "difference is dominated by where the crystal ends; measured to be "
                         "77.5%% of the apparent positive-control signal)")
    ap.add_argument("--min-pocket-coverage", type=float, default=0.80,
                    dest="min_pocket_coverage",
                    help="Hard-fail if apo and control share less than this fraction of the "
                         "pocket's resolved residues (default 0.80).")
    ap.add_argument("--stride", type=int, default=1,
                    help="read every Nth saved frame (memory relief for very long runs). "
                         "Default 1 = every saved frame. This does NOT change the simulation's "
                         "output cadence; any value > 1 is recorded in summary.json and makes "
                         "the run DIAGNOSTIC_ONLY, because the frozen protocol analyses every "
                         "saved frame.")
    args = ap.parse_args()
    args.allow_incomplete_diagnostic = bool(args.allow_incomplete_diagnostic or args.allow_incomplete)
    # Striding does not relax completion enforcement -- it only marks the OUTPUT as diagnostic,
    # because the frozen protocol analyses every saved frame.
    diagnostic_only = bool(args.allow_incomplete_diagnostic or args.stride > 1)
    if args.stride > 1:
        print(f"[analyze] WARNING: --stride {args.stride} subsamples the frozen trajectory "
              "cadence; results are marked DIAGNOSTIC_ONLY / NOT_FOR_SCIENTIFIC_INTERPRETATION.")

    md, np, pd, plt = _imports()
    pocket = load_pocket(args.pocket)
    regions = analysis_regions(pocket)
    parity_resseqs = sorted(set(r for vals in regions.values() for r in vals))
    primary_resseqs = regions.get("supported_ge2of3") or regions.get("pocket") or parity_resseqs
    thresholds = _protocol_thresholds()
    iface = list(pocket.get("interface_chain_indices", [0, 1]))
    apo_pdb, ctrl_pdb = pocket["apo_pdb"], pocket.get("control_pdb")

    out = Path(args.outdir); adir = out / "analysis"; adir.mkdir(parents=True, exist_ok=True)
    rows, sasa_pool, skipped = [], {}, []
    # role -> pdb; keep labels so the report reads apo/control not raw ids
    role_pdb = [("apo", apo_pdb)] + ([("control", ctrl_pdb)] if ctrl_pdb else [])

    # ---- pocket parity: apo and control MUST be measured over the same atoms ----
    role_tops = {}
    for role, pdb in role_pdb:
        tp = out / pdb / "system_solvated.pdb"
        if tp.exists():
            role_tops[role] = _protein_top(md, tp)
    allow_keys, parity_report = (None, {"skipped": "only one role present"})
    if len(role_tops) > 1:
        allow_keys, parity_report = pocket_parity(md, role_tops, parity_resseqs, iface,
                                                  min_coverage=args.min_pocket_coverage,
                                                  exclude_termini=not args.keep_termini)
    (adir / "pocket_parity.json").write_text(json.dumps(parity_report, indent=2), encoding="utf-8")

    for role, pdb in role_pdb:
        base = out / pdb
        top = base / "system_solvated.pdb"
        if not top.exists():
            print(f"[skip] {pdb} ({role}): no system_solvated.pdb (run run_md.py --run {role})"); continue
        sasa_pool[role] = []
        for rep_dir in sorted(base.glob("rep*")):
            dcd = rep_dir / "production.dcd"
            if not dcd.exists() or dcd.stat().st_size < 100_000:
                reason = "missing/empty DCD"
                skipped.append({"role": role, "pdb": pdb, "replicate": rep_dir.name, "reason": reason})
                print(f"[skip] {pdb}/{rep_dir.name}: {reason}"); continue
            completion = validate_scientific_replicate(rep_dir, expected_pdb=pdb, expected_role=role)
            done_ok, done_reason, done_payload = (
                completion["ok"], "; ".join(completion["issues"]) or "complete", completion["done"]
            )
            if not done_ok and not args.allow_incomplete_diagnostic:
                skipped.append({"role": role, "pdb": pdb, "replicate": rep_dir.name,
                                "reason": done_reason, "completion": completion})
                print(f"[skip] {pdb}/{rep_dir.name}: incomplete ({done_reason})"); continue
            print(f"[analyze] {role} {pdb}/{rep_dir.name} ...")
            r = analyze_replicate(dcd, top, primary_resseqs, iface, allow_keys=allow_keys,
                                  regions=regions, thresholds=thresholds,
                                  done_payload=done_payload, stride=args.stride,
                                  primary_region_name=(
                                      "supported_ge2of3" if "supported_ge2of3" in regions
                                      else next(iter(regions))))
            if done_ok:
                sasa_pool[role].extend(r.pop("_sasa_series"))
            else:
                r.pop("_sasa_series", None)
            overall_conv = [
                m.get("convergence", {}).get("overall_status")
                for m in r.get("regions", {}).values()
            ]
            r.update({
                "role": role, "pdb": pdb, "replicate": rep_dir.name,
                "completion_status": "PASS" if done_ok else "DIAGNOSTIC_ONLY",
                "completion_issues": completion["issues"],
                "convergence": {
                    "overall_status": "DRIFTING_BLOCKS" if "DRIFTING_BLOCKS" in overall_conv
                    else ("STABLE_BLOCKS" if "STABLE_BLOCKS" in overall_conv else "INSUFFICIENT_DATA")
                },
            })
            if not done_ok:
                r["diagnostic_mark"] = DIAGNOSTIC_MARK
                skipped.append({"role": role, "pdb": pdb, "replicate": rep_dir.name,
                                "reason": done_reason, "diagnostic_analyzed": True})
            rows.append(r)

    if skipped and not args.allow_incomplete_diagnostic:
        (adir / "skipped_replicates.json").write_text(json.dumps(skipped, indent=2), encoding="utf-8")
        sys.exit("Incomplete/corrupt trajectories were present. Refusing scientific analysis by default. "
                 "Use --allow-incomplete-diagnostic only for NON-SCIENTIFIC / DIAGNOSTIC ONLY analysis.")

    if not rows:
        (adir / "skipped_replicates.json").write_text(json.dumps(skipped, indent=2), encoding="utf-8")
        sys.exit("No complete trajectories analyzed. Run run_md.py first or pass --allow-incomplete-diagnostic "
                 "only for debugging. See outputs/analysis/skipped_replicates.json.")
    df = pd.DataFrame(rows)
    df.to_csv(adir / "per_replicate.csv", index=False)

    # ---- positive-control gate: control(open) pocket SASA vs apo(closed) ----
    verdict = {
        "interpretable": False,
        "reason": "apo/control complete pair unavailable; positive-control comparison requires both roles",
    }
    if sasa_pool.get("apo") and sasa_pool.get("control"):
        apo = np.array(sasa_pool["apo"]); holo = np.array(sasa_pool["control"])
        sep = float(holo.mean() - apo.mean())
        pooled_sd = np.sqrt((apo.std()**2 + holo.std()**2) / 2) or 1e-9
        d = sep / pooled_sd
        apo_reps = [r["pocket_sasa_mean_nm2"] for r in rows if r["role"] == "apo"]
        holo_reps = [r["pocket_sasa_mean_nm2"] for r in rows if r["role"] == "control"]
        n_apo, n_holo = len(apo_reps), len(holo_reps)
        apo_med = float(np.median(apo_reps)) if apo_reps else float("nan")
        per_rep_ok = bool(holo_reps and apo_reps and all(h > apo_med for h in holo_reps))
        control_ok = (holo.mean() > apo.mean()) and (abs(d) > 0.5) and per_rep_ok
        verdict = {
            "interpretable": bool(control_ok),
            "apo_pocket_sasa_nm2": float(apo.mean()), "control_pocket_sasa_nm2": float(holo.mean()),
            "control_minus_apo_nm2": sep, "cohens_d": float(d),
            "cohens_d_caveat": ("Cohen's d is over autocorrelated MD frames pooled across replicates; "
                                "DESCRIPTIVE effect size, not an n=frames test. The independent unit "
                                "is the replicate."),
            "n_apo_replicates": n_apo, "n_control_replicates": n_holo,
            "apo_replicate_means_nm2": [float(x) for x in apo_reps],
            "control_replicate_means_nm2": [float(x) for x in holo_reps],
            "per_replicate_consistent": per_rep_ok,
            "reason": (("Positive control PASSED: the control(open) pocket reads larger than "
                        "apo(closed) in pooled SASA (Cohen's d %.2f) AND in every control replicate "
                        "vs the apo median (%d control / %d apo) -> the metric can detect opening, so "
                        "an apo result is trustworthy." % (d, n_holo, n_apo)) if control_ok else
                       ("Positive control FAILED: control and apo pockets are not cleanly separated "
                        "(pooled Cohen's d %.2f; per-replicate consistent=%s over %d control / %d apo) "
                        "-> DO NOT report apo as a negative; extend sampling or use fpocket/MDpocket/"
                        "enhanced sampling." % (d, per_rep_ok, n_holo, n_apo))),
        }
        plt.figure(figsize=(6, 4))
        plt.hist(apo, bins=40, alpha=0.6, label=f"{apo_pdb} apo (closed)")
        plt.hist(holo, bins=40, alpha=0.6, label=f"{ctrl_pdb} control (open, ligand stripped)")
        plt.xlabel(f"{pocket['pocket_name']} pocket SASA (nm^2)"); plt.ylabel("frames"); plt.legend()
        plt.title("Positive control: pocket openness, control vs apo"); plt.tight_layout()
        plt.savefig(adir / "pocket_sasa_control.png", dpi=140); plt.close()

    caveats = [c for c in (_prep_caveat(out, apo_pdb), _prep_caveat(out, ctrl_pdb) if ctrl_pdb else None) if c]
    any_pbc = bool(df["pbc_artifact_suspected"].any())
    any_duplicate_time = bool(df["duplicate_log_times"].any()) if "duplicate_log_times" in df else False
    any_duplicate_frames = bool((df["frame_count_status"] == "too_many_frames_duplicate_risk").any()) \
        if "frame_count_status" in df else False
    trajectory_control = evaluate_control_interpretability(rows)
    replica_aggregation = {
        "open_like_fraction": aggregate_replicates(rows, ("openness", "open_like_fraction")),
        "pocket_rmsf_mean_nm": aggregate_replicates(rows, ("pocket_rmsf_mean_nm",)),
        "pocket_sasa_mean_nm2": aggregate_replicates(rows, ("pocket_sasa_mean_nm2",)),
    }
    summary = {"pocket": pocket["pocket_name"], "per_replicate": rows,
               "diagnostic_only": bool(diagnostic_only),
               "diagnostic_mark": DIAGNOSTIC_MARK if diagnostic_only else None,
               "analysis_provenance": analysis_provenance(out, args, rows),
               "positive_control": verdict,
               "control_interpretability_gate": trajectory_control,
               "replica_aggregation": replica_aggregation,
               "equil_ns_discarded": EQUIL_NS,
               "analysis_regions": regions,
               "rmsd_protocol": {
                   "global_rmsd": {
                       "field": "rmsd_mean_nm / rmsd_max_nm",
                       "alignment_selection": "protein CA excluding primary pocket CA (scaffold)",
                       "measurement_selection": "same scaffold CA set",
                       "superposition": "optimal (Kabsch/QCP) on the scaffold set",
                       "reference": "frame 0 after PBC imaging",
                       "units": "nm",
                       "pbc_preprocessing": "image_molecules or make_molecules_whole before alignment",
                   },
                   "region_rmsd_scaffold_aligned": {
                       "field": "regions.<name>.region_rmsd_scaffold_aligned_mean_nm",
                       "alignment_selection": "protein CA excluding primary pocket CA (scaffold)",
                       "measurement_selection": "region CA measured on the SCAFFOLD-ALIGNED frames",
                       "superposition": "scaffold transform PRESERVED; the region is NOT re-superposed",
                       "retains": "region displacement relative to the scaffold, plus internal deformation",
                       "reference": "frame 0 after PBC imaging and scaffold alignment",
                       "units": "nm",
                   },
                   "region_internal_rmsd": {
                       "field": "regions.<name>.region_internal_rmsd_mean_nm",
                       "alignment_selection": "the region CA set itself",
                       "measurement_selection": "region CA after re-superposing on the region",
                       "superposition": "optimal (Kabsch/QCP) on the region set",
                       "retains": "internal deformation ONLY; relative displacement is removed by construction",
                       "reference": "frame 0 after PBC imaging",
                       "units": "nm",
                   },
                   "repair_note_2026_08_16": (
                       "Before this repair a single field named local_rmsd was computed with "
                       "mdtraj rmsd(atom_indices=region), which re-superposes on the region, "
                       "while the emitted metadata claimed 'region CA after scaffold alignment'. "
                       "A region rigidly displaced 0.5 nm against a fixed scaffold read 0.000 nm. "
                       "The two quantities are now computed and named separately."
                   ),
               },
               "sasa_protocol": {
                   "scope": "frozen experiment uses interface_chain_indices from pocket JSON; current frozen pocket is chain index 0",
                   "method": "mdtraj Shrake-Rupley in protein context, atom-key parity across apo/control",
               },
               "openness_thresholds": thresholds,
               "pbc_artifact_suspected_any": any_pbc,
               "duplicate_log_times_any": any_duplicate_time,
               "duplicate_frame_count_risk_any": any_duplicate_frames,
               "skipped_replicates": skipped,
               "prep_caveats": caveats}
    (adir / "summary.json").write_text(json.dumps(summary, indent=2))

    # ---- human-readable report ----
    lines = [f"# PCNA MD validation - analysis report ({pocket['pocket_name']})", "",
             f"PBC-artifact suspected in any replicate (frame-to-frame jump > {PBC_JUMP_NM} nm): "
             f"**{any_pbc}**",
             f"Duplicate frame-count risk in any complete replicate: **{any_duplicate_frames}**",
             f"Skipped incomplete/missing replicates: **{len(skipped)}**", "",
             "## Per-replicate", "",
             "| role | pdb | rep | RMSD mean (nm) | max frame-jump (nm) | pocket RMSF (nm) | "
             "pocket SASA (nm^2) | open-like fraction | frame count | PBC-artifact? |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        open_frac = r.get("openness", {}).get("open_like_fraction")
        open_txt = f"{open_frac:.3f}" if isinstance(open_frac, float) else "n/a"
        lines.append(f"| {r['role']} | {r['pdb']} | {r['replicate']} | {r['rmsd_mean_nm']:.3f} | "
                     f"{r['max_frame_jump_nm']:.3f} | {r['pocket_rmsf_mean_nm']:.3f} | "
                     f"{r['pocket_sasa_mean_nm2']:.1f} | {open_txt} | "
                     f"{r.get('frame_count_status', 'unchecked')} | {r['pbc_artifact_suspected']} |")
    lines += ["", "## Positive-control gate (the anti-false-negative check)", "",
              "The production gate uses the trajectory-derived control gate below; pooled "
              "apo/control SASA separation is descriptive only and cannot satisfy Gate-6.",
              "",
              f"- trajectory control gate: **{trajectory_control['status']}**",
              f"- qualifying control replicates: "
              f"{trajectory_control['qualifying_control_replicates']}/"
              f"{trajectory_control['minimum_control_replicates']}",
              f"- static frame-zero separation used: "
              f"{trajectory_control['uses_frame_zero_or_static_apo_control_difference']}",
              f"- reason: {trajectory_control['reason']}",
              "",
              "## Descriptive apo/control SASA contrast (not a gate)", "",
              f"- apo     ({apo_pdb}) pocket SASA:  {verdict.get('apo_pocket_sasa_nm2','n/a')}",
              f"- control ({ctrl_pdb}) pocket SASA:  {verdict.get('control_pocket_sasa_nm2','n/a')}",
              f"- control - apo: {verdict.get('control_minus_apo_nm2','n/a')}  "
              f"(Cohen's d {verdict.get('cohens_d','n/a')})",
              f"- independent replicates: {verdict.get('n_control_replicates','n/a')} control / "
              f"{verdict.get('n_apo_replicates','n/a')} apo; per-replicate consistent: "
              f"{verdict.get('per_replicate_consistent','n/a')}",
              f"- **Interpretable: {verdict['interpretable']}**", f"- {verdict['reason']}",
              f"- _Caveat:_ {verdict.get('cohens_d_caveat','')}", ""]
    if caveats:
        lines += ["## Structure-prep caveats (read the gate WITH these)", ""]
        for c in caveats:
            lines.append(f"- **{c['pdb']}**: biological assembly '{c['assembly']}', "
                         f"{c['internal_residues_rebuilt']} internal residues rebuilt by PDBFixer. "
                         f"(8GLA is 3.77 A - side-chain rotamers are modeled, not observed; treat "
                         f"pocket SASA magnitude as approximate.)")
        lines.append("")
    (adir / "REPORT.md").write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\nWrote {adir/'REPORT.md'}, summary.json, per_replicate.csv, pocket_sasa_control.png")


if __name__ == "__main__":
    main()
