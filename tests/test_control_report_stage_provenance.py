"""Regression test for the Control-20 forensic-audit provenance fix to md_workflow.py.

CONTROL_INTERPRETABILITY_REPORT.md is written to a FIXED path regardless of which MD stage
(control5, control20, ...) produced it. Before this patch, nothing in the file recorded which
outdir/stage produced a given verdict, so a later stage's report silently overwrote an earlier
stage's DISTINCT verdict at the same path -- the only reason the real Control-5 FAIL result
survived was that a human manually copied the file to a hand-named backup before running
Control-20. This test pins the enforced replacement: write_control_report() must now (a) record
the source outdir in the report, and (b) archive the outgoing report under a timestamped name
whenever the outdir or verdict is about to change.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"


def _load_workflow():
    spec = importlib.util.spec_from_file_location("md_workflow_provenance_test", MD / "md_workflow.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["md_workflow_provenance_test"] = mod
    spec.loader.exec_module(mod)
    return mod


wf = _load_workflow()


def test_write_control_report_archives_prior_distinct_stage(tmp_path, monkeypatch):
    # Redirect the module's report/archive location into tmp_path so this test cannot touch
    # the real repository's CONTROL_INTERPRETABILITY_REPORT.md.
    monkeypatch.setattr(wf, "HERE", tmp_path)

    outdir_a = tmp_path / "outputs_control5"
    outdir_b = tmp_path / "outputs_control5_extended"
    outdir_a.mkdir()
    outdir_b.mkdir()

    monkeypatch.setattr(wf, "control5_pass", lambda outdir: (False, ["stage A issue"]))
    wf.write_control_report(argparse.Namespace(outdir=str(outdir_a)))
    report = tmp_path / "CONTROL_INTERPRETABILITY_REPORT.md"
    text_a = report.read_text(encoding="utf-8")
    assert "CONTROL INTERPRETABLE: FAIL" in text_a
    assert f"Source outdir: {outdir_a}" in text_a
    assert not list(tmp_path.glob("CONTROL_INTERPRETABILITY_REPORT_ARCHIVED_*.md")), (
        "nothing to archive on the first write")

    # Stage B: a DIFFERENT outdir with a DIFFERENT verdict overwrites the fixed path.
    monkeypatch.setattr(wf, "control5_pass", lambda outdir: (True, []))
    wf.write_control_report(argparse.Namespace(outdir=str(outdir_b)))
    text_b = report.read_text(encoding="utf-8")
    assert "CONTROL INTERPRETABLE: PASS" in text_b
    assert f"Source outdir: {outdir_b}" in text_b

    archived = list(tmp_path.glob("CONTROL_INTERPRETABILITY_REPORT_ARCHIVED_*.md"))
    assert len(archived) == 1, f"expected exactly one archived report, found {archived}"
    archived_text = archived[0].read_text(encoding="utf-8")
    assert "CONTROL INTERPRETABLE: FAIL" in archived_text
    assert str(outdir_a) in archived_text
    assert "FAIL" in archived[0].name and outdir_a.name in archived[0].name


def test_write_control_report_no_archive_when_same_outdir_and_verdict(tmp_path, monkeypatch):
    monkeypatch.setattr(wf, "HERE", tmp_path)
    outdir = tmp_path / "outputs_control5"
    outdir.mkdir()

    monkeypatch.setattr(wf, "control5_pass", lambda o: (False, ["issue"]))
    wf.write_control_report(argparse.Namespace(outdir=str(outdir)))
    # Re-running the SAME stage with the SAME verdict (e.g. re-analysis, no new data) must not
    # spuriously archive a report against itself.
    wf.write_control_report(argparse.Namespace(outdir=str(outdir)))
    assert not list(tmp_path.glob("CONTROL_INTERPRETABILITY_REPORT_ARCHIVED_*.md"))
