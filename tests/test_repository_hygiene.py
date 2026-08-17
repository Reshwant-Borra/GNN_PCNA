"""Repository hygiene guards.

Two of these exist because of defects found on 2026-08-16:
  * a live Telegram bot token was hard-coded in start_gateway.sh and is in git history;
  * running the test suite rewrote tracked figures under paper/figures/, which also dirties
    the working tree that the MD production authorization checks.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = [
    (r"\b\d{8,10}:AA[A-Za-z0-9_-]{30,}\b", "Telegram bot token"),
    (r"\bsk-[A-Za-z0-9]{20,}\b", "OpenAI-style API key"),
    (r"\bghp_[A-Za-z0-9]{30,}\b", "GitHub personal access token"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS access key id"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b", "Slack token"),
]


def _tracked_files() -> list[Path]:
    out = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"], text=True)
    return [ROOT / p for p in out.split("\0") if p]


def test_no_live_credentials_are_committed():
    offenders = []
    for path in _tracked_files():
        if path.suffix.lower() in (".png", ".jpg", ".pdf", ".docx", ".gz", ".zip",
                                   ".ckpt", ".pt", ".npy", ".dcd", ".cif"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="strict")
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, label in SECRET_PATTERNS:
            if re.search(pattern, text):
                # report the file and the KIND only -- never the value
                offenders.append(f"{path.relative_to(ROOT)}: {label}")
    assert not offenders, f"committed credentials detected: {offenders}"


def test_gateway_reads_its_token_from_the_environment():
    src = (ROOT / "start_gateway.sh").read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN" in src
    assert not re.search(r"TELEGRAM_BOT_TOKEN=\S*\d{6,}:", src), \
        "the token must not be assigned a literal value"
    assert "revoke" in src.lower() and "rotate" in src.lower(), \
        "the rotation requirement must stay documented next to the change"
    assert "git history" in src.lower()


def test_provenance_gaps_document_the_rotation_requirement():
    # The security note lives in the script; the reproducibility gaps live here.
    text = (ROOT / "PROVENANCE_GAPS.md").read_text(encoding="utf-8")
    assert "FROZEN_HANDOFF_REPRODUCIBILITY" in text
    assert "FULL_RETRAINING_REPRODUCIBILITY" in text
    assert "NOT CLOSED" in text
    assert "best_pcna_v3.ckpt" in text
    assert "No checkpoint was invented" in text


def test_no_office_lock_or_scratch_files_are_tracked():
    bad = []
    for path in _tracked_files():
        name = path.name
        if name.startswith("~$") or name == ".DS_Store" or name.endswith(".tmp"):
            bad.append(str(path.relative_to(ROOT)))
        if name in ("_live_demo_scratch.py", "live_type_demo.py"):
            bad.append(str(path.relative_to(ROOT)))
    assert not bad, f"accidental files are tracked: {bad}"


def test_gitattributes_pins_line_endings_for_provenance_files():
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    for suffix in ("*.json", "*.sha256", "*.py", "*.md"):
        assert re.search(rf"^{re.escape(suffix)}\s+text eol=lf", attrs, re.M), \
            f"{suffix} must be pinned to LF"
    # frozen historical evidence must be byte-preserved
    for tree in ("artifacts/**", "outputs/**", "reports/**"):
        assert re.search(rf"^{re.escape(tree)}\s+-text", attrs, re.M), \
            f"{tree} must be byte-preserved"


def test_paper_engine_output_dir_is_overridable():
    """So tests cannot write into the tracked paper/ tree."""
    src = (ROOT / "paper_engine" / "config.py").read_text(encoding="utf-8")
    assert "PAPER_ENGINE_PAPER_DIR" in src
    assert 'os.environ.get("PAPER_ENGINE_PAPER_DIR"' in src


def test_gate6_decision_is_gitignored():
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "md_validation_4070/GATE6_DECISION.json" in ignored, (
        "a Gate-6 approval must never be committed")


@pytest.mark.parametrize("path", [
    "md_validation_4070/GATE6_DECISION.json",
    "md_validation_4070/outputs/analysis/summary.json",
])
def test_no_result_or_approval_artifact_is_committed(path):
    out = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", path], text=True)
    assert not out.strip(), f"{path} must not be tracked"
