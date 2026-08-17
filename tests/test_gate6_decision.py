"""Gate 6 must be a structured human decision, not a substring match on prose.

The pre-repair implementation scanned research_os_memory/HUMAN_DECISIONS.md for the words
"gate 6" and "approved" anywhere in the document, with a negative list that never matched the
phrasings people actually write. Reproduced 2026-08-16: it authorized production for both
"Gate 6: NOT YET APPROVED" and "Gate 5 approved; Gate 6 pending".
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"


def _load():
    spec = importlib.util.spec_from_file_location("md_workflow_under_test", MD / "md_workflow.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["md_workflow_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


wf = _load()

# The exact strings the audit requires. Only the last may authorize production.
NEGATIVE_TEXTS = [
    "Gate 6: NOT YET APPROVED",
    "Gate 6 pending",
    "Gate 6 approval withheld",
    "Gate 5 approved; Gate 6 pending",
]
POSITIVE_TEXT = "Gate 6 approved by human reviewer"


@pytest.mark.parametrize("text", NEGATIVE_TEXTS + [POSITIVE_TEXT])
def test_free_text_can_never_authorize_production(tmp_path, monkeypatch, text):
    """No prose whatsoever -- not even the affirmative one -- grants Gate 6."""
    decisions = ROOT / "research_os_memory" / "HUMAN_DECISIONS.md"
    original = decisions.read_text(encoding="utf-8") if decisions.exists() else None
    try:
        decisions.parent.mkdir(parents=True, exist_ok=True)
        decisions.write_text(text + "\n", encoding="utf-8")
        monkeypatch.setattr(wf, "GATE6_DECISION_PATH", tmp_path / "GATE6_DECISION.json")
        assert wf.gate6_approved() is False, (
            f"prose {text!r} must not authorize production; authorization requires a "
            "structured GATE6_DECISION.json")
    finally:
        if original is not None:
            decisions.write_text(original, encoding="utf-8")
        elif decisions.exists():
            decisions.unlink()


def _valid_payload(**over):
    payload = {
        "schema_version": 1,
        "kind": "PCNA_MD_GATE6_DECISION",
        "approved": True,
        "approved_by": "R. Borra (human reviewer)",
        "approved_utc": "2026-08-17T12:00:00+00:00",
        "commit": wf.run_text(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
        "control5_report_sha256": wf._sha256_or_none(MD / "CONTROL_INTERPRETABILITY_REPORT.md"),
        "analysis_protocol_sha256": wf._sha256_or_none(MD / "FROZEN_MD_ANALYSIS_PROTOCOL.json"),
        "notes": "reviewed control-5 interpretability report",
    }
    payload.update(over)
    return payload


def _write(tmp_path, payload):
    p = tmp_path / "GATE6_DECISION.json"
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


def test_missing_decision_fails_closed(tmp_path):
    d = wf.gate6_decision(tmp_path / "nope.json")
    assert d["approved"] is False
    assert any("no Gate-6 decision artifact" in r for r in d["reasons"])


def test_invalid_json_fails_closed(tmp_path):
    p = tmp_path / "GATE6_DECISION.json"
    p.write_text("{not json", encoding="utf-8")
    d = wf.gate6_decision(p)
    assert d["approved"] is False
    assert any("not valid JSON" in r for r in d["reasons"])


@pytest.mark.parametrize("approved", [False, None, "true", "yes", 1])
def test_non_true_approved_fails_closed(tmp_path, approved):
    d = wf.gate6_decision(_write(tmp_path, _valid_payload(approved=approved)),
                          strict_bindings=False)
    assert d["approved"] is False
    assert any("not boolean true" in r for r in d["reasons"])


def test_wrong_kind_fails_closed(tmp_path):
    d = wf.gate6_decision(_write(tmp_path, _valid_payload(kind="SOMETHING_ELSE")),
                          strict_bindings=False)
    assert d["approved"] is False
    assert any("kind" in r for r in d["reasons"])


def test_missing_required_fields_fails_closed(tmp_path):
    payload = _valid_payload()
    del payload["approved_by"]
    del payload["notes"]
    d = wf.gate6_decision(_write(tmp_path, payload), strict_bindings=False)
    assert d["approved"] is False
    assert any("missing required fields" in r for r in d["reasons"])


def test_empty_approver_fails_closed(tmp_path):
    d = wf.gate6_decision(_write(tmp_path, _valid_payload(approved_by="   ")),
                          strict_bindings=False)
    assert d["approved"] is False
    assert any("approved_by is empty" in r for r in d["reasons"])


def test_expired_decision_fails_closed(tmp_path):
    d = wf.gate6_decision(
        _write(tmp_path, _valid_payload(expires_utc="2020-01-01T00:00:00+00:00")),
        strict_bindings=False)
    assert d["approved"] is False
    assert any("expired" in r for r in d["reasons"])


def test_wrong_commit_fails_closed(tmp_path):
    d = wf.gate6_decision(_write(tmp_path, _valid_payload(commit="0" * 40)))
    assert d["approved"] is False
    assert any("commit" in r for r in d["reasons"])


def test_wrong_protocol_hash_fails_closed(tmp_path):
    d = wf.gate6_decision(_write(tmp_path, _valid_payload(analysis_protocol_sha256="0" * 64)))
    assert d["approved"] is False
    assert any("analysis_protocol_sha256" in r for r in d["reasons"])


def test_wrong_control_report_hash_fails_closed(tmp_path):
    d = wf.gate6_decision(_write(tmp_path, _valid_payload(control5_report_sha256="0" * 64)))
    assert d["approved"] is False
    assert any("control5_report_sha256" in r or "control-5 interpretability report" in r
               for r in d["reasons"])


def test_fully_valid_decision_authorizes(tmp_path):
    """Only a complete, correctly bound, explicitly true decision authorizes production."""
    d = wf.gate6_decision(_write(tmp_path, _valid_payload()), strict_bindings=False)
    assert d["approved"] is True, d["reasons"]
    assert d["reasons"] == []


def test_no_gate6_decision_exists_in_repository():
    """Nothing in this repository may ship a granted Gate-6 approval."""
    live = MD / "GATE6_DECISION.json"
    assert not live.exists(), (
        f"{live} must not exist in the repository. Gate 6 is granted on the cloud instance "
        "by a human after reviewing control-5, never committed pre-emptively.")
    assert wf.gate6_approved() is False


def test_template_is_inert():
    """The template must be present, and must not itself be an approval."""
    template = MD / "GATE6_DECISION.template.json"
    assert template.exists()
    payload = json.loads(template.read_text())
    assert payload["approved"] is False
    assert payload["approved_by"] == ""
