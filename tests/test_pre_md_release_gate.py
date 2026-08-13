"""Regression tests for the four pre-MD release blockers (audit 2026-08).

Each test corresponds to a blocker that was confirmed by execution and survived an
adversarial refutation pass. They are deliberately cheap so they can gate every run.

    python -m pytest tests/test_pre_md_release_gate.py -q
"""

from __future__ import annotations

import ast
import csv
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
MD = Path("C:/Users/advay/GNN_PNCA/md_validation_4070")


# --------------------------------------------------------------------------------------
# B1 — run_v3_inference.py crashed with KeyError('auroc') and set -e aborted the pipeline
# --------------------------------------------------------------------------------------

def _summary_rows():
    p = REPO / "results" / "per_structure" / "summary_table.csv"
    if not p.exists():
        pytest.skip(f"missing {p}")
    with open(p, encoding="utf-8", errors="replace") as fh:
        return list(csv.DictReader(fh))


def test_v1_auroc_block_tolerates_the_committed_header():
    """The exact expression that used to raise KeyError('auroc') must not raise."""
    rows = _summary_rows()
    assert rows, "summary_table.csv is empty"
    key = next((k for k in ("auroc", "auto_ligand_auroc_sanity") if k in rows[0]), None)
    assert key is not None, (
        f"neither 'auroc' nor 'auto_ligand_auroc_sanity' present; columns={list(rows[0])}"
    )
    out = {}
    for r in rows:
        try:
            out[r["pdb"]] = float(r.get(key))
        except (TypeError, ValueError):
            continue
    assert isinstance(out, dict)


def test_every_column_run_v3_inference_reads_exists():
    """Cheap schema guard: no r["..."] subscript on a CSV row may name a missing column."""
    rows = _summary_rows()
    available = set(rows[0]) | {"pdb"}
    src = (REPO / "scripts" / "run_v3_inference.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    missing = []
    for node in ast.walk(tree):
        # match  r["col"]  where r is the DictReader row variable
        if (isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name) and node.value.id == "r"
                and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str)):
            if node.slice.value not in available:
                missing.append((node.lineno, node.slice.value))
    assert not missing, f"run_v3_inference.py subscripts absent CSV columns: {missing}"


# --------------------------------------------------------------------------------------
# B2 — a pre-virtual-node-fix checkpoint loaded silently
# --------------------------------------------------------------------------------------

def test_inference_refuses_a_stale_checkpoint():
    """Inference must exit non-zero (naming it STALE) on a pre-fix checkpoint."""
    stale = REPO / "checkpoints" / "pcna_reproduced" / "best.ckpt"
    if not stale.exists():
        pytest.skip("no checkpoint to test against")
    proc = subprocess.run(
        [sys.executable, "scripts/run_v3_inference.py", "--ckpt", str(stale)],
        cwd=REPO, capture_output=True, text=True, timeout=600,
    )
    combined = proc.stdout + proc.stderr
    assert proc.returncode != 0, "stale checkpoint was accepted without complaint"
    assert "STALE" in combined, f"exit was non-zero but no STALE diagnostic:\n{combined[-800:]}"


def test_stale_checkpoint_override_is_explicit():
    src = (REPO / "scripts" / "run_v3_inference.py").read_text(encoding="utf-8")
    assert "--allow-stale-ckpt" in src
    assert "VIRTUAL_NODE_FIX_EPOCH" in src


# --------------------------------------------------------------------------------------
# B3 — the mandated retrain was unseeded, so no candidate pocket was reproducible
# --------------------------------------------------------------------------------------

def test_finetune_exposes_and_applies_a_seed():
    src = (REPO / "scripts" / "finetune_v3_fixed.py").read_text(encoding="utf-8")
    assert '"--seed"' in src or "'--seed'" in src, "finetune_v3_fixed.py has no --seed"
    for call in ("random.seed(", "np.random.seed(", "torch.manual_seed("):
        assert call in src, f"missing {call}"
    tree = ast.parse(src)
    main_fn = next(n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "main")
    # seeding must happen before any other statement that could consume RNG
    seeded_by = None
    for i, stmt in enumerate(main_fn.body[:12]):
        if "manual_seed" in ast.dump(stmt):
            seeded_by = i
            break
    assert seeded_by is not None and seeded_by < 8, (
        "torch.manual_seed must be near the top of main(), before model construction"
    )


@pytest.mark.slow
def test_two_seeded_retrains_are_bitwise_identical(tmp_path):
    """The real determinism proof. Slow: runs two short trainings."""
    import hashlib
    outs = []
    for i in range(2):
        out = tmp_path / f"run{i}" / "best.ckpt"
        out.parent.mkdir(parents=True)
        proc = subprocess.run(
            [sys.executable, "scripts/finetune_v3_fixed.py",
             "--epochs", "2", "--seed", "42", "--out", str(out)],
            cwd=REPO, capture_output=True, text=True, timeout=3600,
        )
        assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
        assert out.exists(), f"no checkpoint written: {proc.stdout[-1000:]}"
        outs.append(hashlib.sha256(out.read_bytes()).hexdigest())
    assert outs[0] == outs[1], f"identical invocations produced different checkpoints: {outs}"


# --------------------------------------------------------------------------------------
# B4 — apo and control pocket SASA were computed over different atom sets
# --------------------------------------------------------------------------------------

class _Res:
    def __init__(self, ci, rs):
        self.chain = type("C", (), {"index": ci})()
        self.resSeq = rs


class _Atom:
    def __init__(self, ci, rs, name, i):
        self.residue = _Res(ci, rs)
        self.name = name
        self.index = i


class _Chain:
    def __init__(self, index, residues):
        self.index = index
        self.residues = residues


class _Top:
    """Minimal mdtraj-topology stand-in: .atoms with .residue/.name/.index, plus .chains."""

    def __init__(self, keys):
        self.atoms = [_Atom(c, r, n, i) for i, (c, r, n) in enumerate(keys)]
        by_chain: dict[int, dict[int, _Res]] = {}
        for a in self.atoms:
            by_chain.setdefault(a.residue.chain.index, {}).setdefault(a.residue.resSeq, a.residue)
        self.chains = [_Chain(ci, list(res.values())) for ci, res in sorted(by_chain.items())]


def _bb(ci, rs):
    return [(ci, rs, n) for n in ("N", "CA", "C", "O")]


def test_pocket_parity_equalises_atom_sets_not_just_residues():
    """The real defect: same residues, different ATOM counts (a terminal OXT).

    Measured on the real prepared assemblies: apo 854 atoms vs control 855, identical
    56 residues, the extra atom being chain1:253:OXT. A residue-level check passes that
    and still compares unequal atom sets, which is what biases control-minus-apo SASA.
    """
    pytest.importorskip("mdtraj")
    sys.path.insert(0, str(MD))
    import analyze_md as am

    resseqs, iface = [25, 253], [0, 1]
    shared = _bb(0, 25) + _bb(0, 253) + _bb(1, 25) + _bb(1, 253)
    apo = _Top(shared)
    ctrl = _Top(shared + [(1, 253, "OXT")])  # terminal oxygen only in the control

    assert len(am.resolved_pocket_residues(apo, resseqs, iface)) == \
           len(am.resolved_pocket_residues(ctrl, resseqs, iface)), "residue sets are equal"
    na = len(am.pocket_selection(apo, resseqs, iface))
    nc = len(am.pocket_selection(ctrl, resseqs, iface))
    assert na != nc, "fixture does not model the atom-count asymmetry"

    # exclude_termini=False isolates the atom-parity behaviour under test; the terminus
    # rule has its own test, and in a 2-residue fixture every residue is a chain end.
    common, report = am.pocket_parity(None, {"apo": apo, "control": ctrl}, resseqs, iface,
                                      min_coverage=0.5, exclude_termini=False)
    assert (1, 253, "OXT") not in common
    assert report["dropped_per_role"]["control"] == ["chain1:253:OXT"]
    assert len(am.pocket_selection(apo, resseqs, iface, allow_keys=common)) == \
           len(am.pocket_selection(ctrl, resseqs, iface, allow_keys=common))


def test_pocket_parity_drops_a_wholly_unmodelled_residue():
    pytest.importorskip("mdtraj")
    sys.path.insert(0, str(MD))
    import analyze_md as am

    resseqs, iface = [25, 255], [0]
    apo = _Top(_bb(0, 25) + _bb(0, 255))
    ctrl = _Top(_bb(0, 25))  # 255 entirely unmodelled
    common, report = am.pocket_parity(None, {"apo": apo, "control": ctrl}, resseqs, iface,
                                      min_coverage=0.4, exclude_termini=False)
    assert not any(k[1] == 255 for k in common)
    assert report["common_residues"] == 1


def test_pocket_parity_hard_fails_below_coverage():
    pytest.importorskip("mdtraj")
    sys.path.insert(0, str(MD))
    import analyze_md as am

    apo = _Top([(0, n, "CA") for n in range(10)])
    ctrl = _Top([(0, 0, "CA"), (0, 1, "CA")])  # only 20% overlap
    with pytest.raises(SystemExit):
        am.pocket_parity(None, {"apo": apo, "control": ctrl}, list(range(10)), [0],
                         min_coverage=0.80)


# --------------------------------------------------------------------------------------
# Pocket plausibility guards + MD system integrity
# --------------------------------------------------------------------------------------

def _mk_rows(spec):
    """spec: list of (cluster, chain, resid, score)."""
    return [{"cluster": c, "chain": ch, "resid": str(r), "score": s} for c, ch, r, s in spec]


def test_sanity_check_rejects_size_blind_tiny_cluster():
    sys.path.insert(0, str(MD / "gnn_pocket_search"))
    import export_handoff as eh

    rows = _mk_rows([(0, "A", i, 0.9) for i in range(3)]        # 3-residue "pocket"
                    + [(1, "A", 100 + i, 0.2) for i in range(30)])
    chosen, members, allr = eh.load_cluster_rows(rows) if hasattr(eh, "load_cluster_rows") else (
        0, [r for r in rows if r["cluster"] == 0], rows)
    with pytest.raises(SystemExit, match="too small"):
        eh.sanity_check_cluster(chosen, members, allr)


def test_sanity_check_rejects_whole_chain_runaway():
    sys.path.insert(0, str(MD / "gnn_pocket_search"))
    import export_handoff as eh

    rows = _mk_rows([(0, "A", i, 0.9) for i in range(200)]
                    + [(1, "A", 900 + i, 0.1) for i in range(5)])
    members = [r for r in rows if r["cluster"] == 0]
    with pytest.raises(SystemExit) as ei:
        eh.sanity_check_cluster(0, members, rows)
    assert "region, not a pocket" in str(ei.value) or "of a chain" in str(ei.value)


def test_sanity_check_rejects_a_coin_flip_margin():
    sys.path.insert(0, str(MD / "gnn_pocket_search"))
    import export_handoff as eh

    rows = _mk_rows([(0, "A", i, 0.500) for i in range(20)]
                    + [(1, "B", 100 + i, 0.499) for i in range(20)])
    members = [r for r in rows if r["cluster"] == 0]
    with pytest.raises(SystemExit, match="not determined by the model"):
        eh.sanity_check_cluster(0, members, rows)


def test_sanity_check_accepts_a_plausible_pocket():
    sys.path.insert(0, str(MD / "gnn_pocket_search"))
    import export_handoff as eh

    rows = _mk_rows([(0, "A", i, 0.90) for i in range(20)]
                    + [(1, "B", 100 + i, 0.40) for i in range(20)]
                    + [(-1, "A", 200 + i, 0.05) for i in range(200)])
    members = [r for r in rows if r["cluster"] == 0]
    diag = eh.sanity_check_cluster(0, members, rows)
    assert diag["n_residues"] == 20


def test_impossible_bond_assertion_exists_and_is_wired():
    src = (MD / "run_md.py").read_text(encoding="utf-8")
    assert "def assert_no_impossible_bonds" in src
    assert "assert_no_impossible_bonds(system, positions" in src, (
        "the assertion must actually run inside make_simulation, not merely be defined"
    )
    assert "full_sequence" in src, "SEQRES transfer (the root-cause fix) is missing"


def test_terminus_exclusion_is_applied():
    sys.path.insert(0, str(MD))
    import analyze_md as am

    apo = _Top(_bb(0, 10) + _bb(0, 11) + _bb(0, 12))
    ctrl = _Top(_bb(0, 10) + _bb(0, 11) + _bb(0, 12))
    common, report = am.pocket_parity(None, {"apo": apo, "control": ctrl}, [10, 11, 12], [0],
                                      min_coverage=0.1, exclude_termini=True)
    # 10 and 12 are chain ends -> excluded; only 11 survives
    assert {k[1] for k in common} == {11}, report
    assert report["excluded_terminus_or_gap_adjacent"] == ["chain0:10", "chain0:12"]


def test_empty_pocket_selection_fails_loudly():
    src = (MD / "analyze_md.py").read_text(encoding="utf-8")
    assert "empty pocket selection" in src, (
        "analyze_replicate must sys.exit on an empty selection rather than emit NaN metrics"
    )
