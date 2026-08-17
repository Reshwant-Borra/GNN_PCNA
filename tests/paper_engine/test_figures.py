"""Tests that figure rendering produces real files with honest provenance."""
import json
from pathlib import Path

from paper_engine import config
from paper_engine.figures import render
from paper_engine.figures.figure_specs import FIGURE_SPECS, MD_FIGURE_SPECS


def test_render_one_figure_creates_file_and_provenance():
    results = render.render_all(only=["baseline_comparison"])
    assert len(results) == 1
    r = results[0]
    assert Path(r.path).exists()
    assert r.reviewer_question  # answers a reviewer question
    assert r.data_sources       # provenance: which real files fed it
    assert "render" in r.command


def test_figures_manifest_written_and_valid():
    render.render_all(only=["dataset_split"])
    manifest = config.FIGURES_DIR / "figures_manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    ids = {f["figure_id"] for f in data["figures"]}
    assert "dataset_split" in ids
    # Manifest must flag validation-only / no-claims.
    assert "no scientific claims" in data["note"].lower()


def test_every_spec_has_a_builder():
    # Static figures must each map to a builder.
    for fid in FIGURE_SPECS:
        assert fid in render.BUILDERS, f"missing builder for {fid}"
    # MD specs are rendered by the md module (not in BUILDERS).
    assert set(MD_FIGURE_SPECS) == {"md_rmsd", "md_rmsf", "md_dccm"}
