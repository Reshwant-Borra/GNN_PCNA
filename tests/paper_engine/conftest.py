"""Keep paper_engine tests out of the tracked paper/ tree.

Found 2026-08-16: `render.render_all(...)` writes straight into the TRACKED paper/figures/
directory, so simply running the test suite rewrote paper/figures/baseline_comparison.png
and paper/figures/dataset_split.png and left the working tree dirty. Tests must not mutate
committed scientific artifacts, and the dirty tree also trips the MD production
authorization's "git dirty state changed after authorization" check.

Redirect every generated artifact into a per-session tmp directory, and assert afterwards
that nothing under paper/figures/ changed.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TRACKED_FIGURES = ROOT / "paper" / "figures"


def _fingerprint() -> dict[str, str]:
    if not TRACKED_FIGURES.is_dir():
        return {}
    return {
        str(p.relative_to(TRACKED_FIGURES)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(TRACKED_FIGURES.rglob("*")) if p.is_file()
    }


@pytest.fixture(autouse=True, scope="session")
def _isolate_paper_outputs(tmp_path_factory):
    sandbox = tmp_path_factory.mktemp("paper_engine_outputs")
    os.environ["PAPER_ENGINE_PAPER_DIR"] = str(sandbox)

    # config may already be imported; rebind its output paths too.
    import importlib
    import paper_engine.config as config
    importlib.reload(config)
    for module in ("paper_engine.figures.render",
                   "paper_engine.figures.md_results",
                   "paper_engine.figures.md"):
        try:
            importlib.reload(importlib.import_module(module))
        except Exception:
            pass

    before = _fingerprint()
    yield sandbox
    after = _fingerprint()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    assert not changed, (
        "paper_engine tests modified tracked files under paper/figures/: "
        f"{changed}. Rendering must go to PAPER_ENGINE_PAPER_DIR.")
