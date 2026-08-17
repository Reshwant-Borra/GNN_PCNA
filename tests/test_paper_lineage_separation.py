"""Historical results must never be usable as current 1W60/8GLA validation.

Three MD lineages exist in this repository and only one of them is the current experiment:
  1. 1AXC 25 ns exploratory, n=1 complete replicate, no valid 8GLA control  -- HISTORICAL
  2. data/md/1W60_production.dcd, no topology, not in a clean clone         -- UNVERIFIED
  3. the frozen 1W60 apo / 8GLA control experiment                          -- NOT YET RUN

paper_engine is downstream reporting. The scientific source of truth is analyze_md.py plus
FROZEN_MD_ANALYSIS_PROTOCOL.json plus the raw trajectory provenance.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"
PAPER = ROOT / "paper"
ENGINE = ROOT / "paper_engine"


def test_manuscript_carries_the_draft_marking():
    text = (PAPER / "manuscript.md").read_text(encoding="utf-8")
    assert "DRAFT_NOT_FOR_SCIENTIFIC_SUBMISSION" in text
    head = text[:4000]
    assert "DRAFT_NOT_FOR_SCIENTIFIC_SUBMISSION" in head, \
        "the marking must be at the top, not buried"
    for required in ("GraphSAGE-3L", "WRONG_LINEAGE", "PocketGNNXL", "1AXC",
                     "has not been run"):
        assert required in head, f"lineage banner is missing {required!r}"


def test_lineage_audit_exists_and_classifies_every_required_category():
    text = (PAPER / "LINEAGE_AUDIT.md").read_text(encoding="utf-8")
    for category in ("CURRENT_CANONICAL", "HISTORICAL_VALID", "STALE", "UNSUPPORTED",
                     "WRONG_LINEAGE", "UNVERIFIED"):
        assert category in text, f"{category} is not used in the lineage audit"
    for category in ("HISTORICAL_ONLY", "FIGURE_ONLY", "REMOVE_FROM_CURRENT_PIPELINE"):
        assert category in text, f"paper_engine path classification is missing {category}"


def test_paper_engine_never_reads_the_current_md_pipeline_outputs():
    """The single most important separation: no historical figure code may read live MD."""
    offenders = []
    for path in ENGINE.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if "md_validation_4070" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, (
        "paper_engine must not read md_validation_4070; it is downstream reporting and must "
        f"consume frozen analysis outputs only. Offenders: {offenders}")


def _code_without_comments(path: Path) -> str:
    """Executable lines only. A comment citing 1AXC as past context is not data coupling."""
    import io
    import tokenize
    src = path.read_text(encoding="utf-8", errors="replace")
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT,):
                continue
            if tok.type == tokenize.STRING and tok.line.strip().startswith(('"""', "'''")):
                continue                      # docstring
            out.append(tok.string)
    except tokenize.TokenError:
        return src
    return " ".join(out)


def test_current_md_pipeline_never_reads_historical_phase5_or_paper_engine():
    """And the converse: the scientific pipeline must not import reporting code or 1AXC data."""
    offenders = []
    for path in (MD / "analyze_md.py", MD / "run_md.py", MD / "md_workflow.py"):
        code = _code_without_comments(path)
        for forbidden in ("paper_engine", "phase5_md", "1AXC", "1axc", "time_crunch"):
            if forbidden in code:
                offenders.append(f"{path.name}: {forbidden}")
    assert not offenders, (
        f"the scientific pipeline must not couple to historical/reporting data: {offenders}")


def test_historical_1axc_figures_are_labelled_as_1axc():
    """A reader must not be able to mistake a 1AXC figure for 1W60/8GLA validation."""
    src = (ENGINE / "figures" / "md_results.py").read_text(encoding="utf-8")
    assert "1AXC" in src
    for marker in ("1AXC", "exploratory"):
        assert marker.lower() in src.lower()
    manifest = (PAPER / "figures" / "figures_manifest.json").read_text(encoding="utf-8")
    for fig_id in ("md_rmsd", "md_rmsf"):
        idx = manifest.index(f'"figure_id": "{fig_id}"')
        window = manifest[idx:idx + 2000]
        assert "1AXC" in window, f"{fig_id} caption must name 1AXC"
        assert "xploratory" in window, f"{fig_id} caption must say exploratory"


def test_no_current_result_is_claimed_for_the_frozen_experiment():
    """The frozen 1W60/8GLA experiment has not been run; nothing may claim otherwise."""
    outputs = MD / "outputs" / "analysis" / "summary.json"
    assert not outputs.exists(), (
        "an analysis summary exists for the frozen experiment; this repair pass ran no MD, "
        "so its presence would mean a result was fabricated or committed")


def test_only_one_official_rmsd_implementation_is_in_the_current_pipeline():
    """paper_engine/figures/md.py is a second RMSD/DCCM implementation. It must stay inert."""
    md_py = ENGINE / "figures" / "md.py"
    if not md_py.exists():
        return                                   # removed entirely: also acceptable
    src = md_py.read_text(encoding="utf-8")
    assert "md_validation_4070" not in src
    # it must fail loudly rather than fabricate when its inputs are absent
    assert "MDUnavailable" in src
    audit = (PAPER / "LINEAGE_AUDIT.md").read_text(encoding="utf-8")
    assert "REMOVE_FROM_CURRENT_PIPELINE" in audit
    assert "paper_engine/figures/md.py" in audit


def test_referenced_but_absent_md_trajectory_is_flagged_not_silently_used():
    trajectory = ROOT / "data" / "md" / "1W60_production.dcd"
    if trajectory.exists():
        pytest.skip("trajectory present in this working tree")
    audit = (PAPER / "LINEAGE_AUDIT.md").read_text(encoding="utf-8")
    assert "1W60_production.dcd" in audit
    assert "UNSUPPORTED" in audit or "UNVERIFIED" in audit


def test_figures_manifest_machine_specific_paths_are_recorded_as_a_defect():
    manifest = (PAPER / "figures" / "figures_manifest.json").read_text(encoding="utf-8")
    if re.search(r"[A-Za-z]:\\\\Users", manifest) or "C:\\\\Users" in manifest:
        audit = (PAPER / "LINEAGE_AUDIT.md").read_text(encoding="utf-8")
        assert "machine-specific absolute Windows paths" in audit, (
            "figures_manifest.json contains machine-specific paths that are not documented")
