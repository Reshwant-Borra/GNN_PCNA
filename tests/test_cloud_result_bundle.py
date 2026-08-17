"""The compact result bundle must carry the science and leave the trajectories behind.

Production DCDs are tens of GB and stay on the cloud instance. `./md.sh bundle` must package
only derived results, and must reference the large sources by SHA-256 so the compact bundle
stays traceable to trajectories that were never transferred.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tarfile
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "md_validation_4070"


def _load():
    spec = importlib.util.spec_from_file_location("md_workflow_bundle", MD / "md_workflow.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["md_workflow_bundle"] = mod
    spec.loader.exec_module(mod)
    return mod


wf = _load()

BIG = b"\x00" * (3 * 1024 * 1024)          # stand-in for a multi-GB trajectory


@pytest.fixture
def outputs(tmp_path):
    out = tmp_path / "outputs"
    adir = out / "analysis"
    adir.mkdir(parents=True)
    (adir / "summary.json").write_text(json.dumps({
        "pocket": "final_consensus_1w60_20260815",
        "diagnostic_only": False,
        "control_interpretability_gate": {"status": "PASS"},
        "per_replicate": [],
    }), encoding="utf-8")
    (adir / "per_replicate.csv").write_text("role,pdb\ncontrol,8GLA\n", encoding="utf-8")
    (adir / "REPORT.md").write_text("# report\n", encoding="utf-8")
    (adir / "pocket_sasa_control.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 100)

    for pdb, role in (("8GLA", "control"), ("1W60", "apo")):
        base = out / pdb
        (base / "prep").mkdir(parents=True)
        (base / "prep" / "prep_audit.json").write_text("{}", encoding="utf-8")
        (base / "pocket_definition.json").write_text("{}", encoding="utf-8")
        (base / "system_solvated.pdb").write_bytes(BIG)
        for rep in ("rep01", "rep02", "rep03"):
            r = base / rep
            r.mkdir()
            (r / "production.dcd").write_bytes(BIG)
            (r / "state.chk").write_bytes(BIG)
            (r / "equilibration.dcd").write_bytes(BIG)
            (r / "DONE.json").write_text(json.dumps({"role": role, "pdb": pdb}), encoding="utf-8")
            (r / "PROVENANCE.json").write_text("{}", encoding="utf-8")
            (r / "EQUILIBRATION.json").write_text('{"accepted": true}', encoding="utf-8")
            (r / "production.log").write_text("#Step\n1\n", encoding="utf-8")
            (r / "equilibration.log").write_text("#Step\n1\n", encoding="utf-8")
    return out


def _bundle(outputs, tmp_path, **over):
    args = types.SimpleNamespace(outdir=str(outputs),
                                 bundle_out=str(tmp_path / "bundle.tar.gz"),
                                 allow_missing_summary=False)
    for k, v in over.items():
        setattr(args, k, v)
    rc = wf.make_bundle(args)
    return rc, Path(args.bundle_out)


def test_bundle_contains_no_trajectories_or_checkpoints(outputs, tmp_path):
    rc, dest = _bundle(outputs, tmp_path)
    assert rc == 0
    with tarfile.open(dest) as tar:
        names = tar.getnames()
    assert names, "bundle must not be empty"
    for name in names:
        assert not name.endswith(".dcd"), f"trajectory leaked into the bundle: {name}"
        assert not name.endswith(".chk"), f"checkpoint leaked into the bundle: {name}"
        assert not name.endswith("system_solvated.pdb"), f"solvated topology leaked: {name}"


def test_bundle_is_small_relative_to_the_raw_data(outputs, tmp_path):
    rc, dest = _bundle(outputs, tmp_path)
    assert rc == 0
    raw = sum(p.stat().st_size for p in outputs.rglob("*")
              if p.is_file() and (p.suffix == ".dcd" or p.name in ("state.chk",
                                                                   "system_solvated.pdb")))
    assert dest.stat().st_size < raw / 50, (
        f"bundle {dest.stat().st_size} B is not small relative to raw {raw} B")


def test_bundle_contains_the_scientific_outputs(outputs, tmp_path):
    rc, dest = _bundle(outputs, tmp_path)
    assert rc == 0
    with tarfile.open(dest) as tar:
        names = set(tar.getnames())
    for required in ("pcna_md_results/analysis/summary.json",
                     "pcna_md_results/analysis/per_replicate.csv",
                     "pcna_md_results/analysis/REPORT.md",
                     "pcna_md_results/analysis/pocket_sasa_control.png",
                     "pcna_md_results/analysis/BUNDLE_MANIFEST.json",
                     "pcna_md_results/8GLA/rep01/DONE.json",
                     "pcna_md_results/8GLA/rep01/PROVENANCE.json",
                     "pcna_md_results/8GLA/rep01/EQUILIBRATION.json",
                     "pcna_md_results/8GLA/rep01/production.log",
                     "pcna_md_results/8GLA/rep01/equilibration.log",
                     "pcna_md_results/8GLA/prep/prep_audit.json"):
        assert required in names, f"missing {required} from bundle"


def test_manifest_hashes_every_large_cloud_resident_source(outputs, tmp_path):
    rc, _ = _bundle(outputs, tmp_path)
    assert rc == 0
    manifest = json.loads((outputs / "analysis" / "BUNDLE_MANIFEST.json").read_text())
    paths = {e["path"] for e in manifest["large_cloud_resident_sources"]}
    assert "8GLA/rep01/production.dcd" in paths
    assert "1W60/rep03/production.dcd" in paths
    assert "8GLA/system_solvated.pdb" in paths
    for entry in manifest["large_cloud_resident_sources"]:
        assert len(entry["sha256"]) == 64
        assert entry["bytes"] > 0
        assert entry["included_in_bundle"] is False
        assert entry["absolute_path_on_cloud_instance"]
    assert manifest["large_cloud_resident_total_bytes"] > 0


def test_manifest_records_code_and_protocol_identity(outputs, tmp_path):
    rc, _ = _bundle(outputs, tmp_path)
    assert rc == 0
    manifest = json.loads((outputs / "analysis" / "BUNDLE_MANIFEST.json").read_text())
    for key in ("analysis_protocol_sha256", "analysis_code_sha256", "run_md_sha256",
                "md_workflow_sha256"):
        assert manifest[key] and len(manifest[key]) == 64
    assert "commit" in manifest["git"]
    assert manifest["kind"] == "PCNA_MD_COMPACT_RESULT_BUNDLE"


def test_bundle_refuses_without_analysis_summary(outputs, tmp_path):
    (outputs / "analysis" / "summary.json").unlink()
    rc, _ = _bundle(outputs, tmp_path)
    assert rc == 1


def test_bundle_flags_diagnostic_only_output(outputs, tmp_path, capsys):
    summary = json.loads((outputs / "analysis" / "summary.json").read_text())
    summary["diagnostic_only"] = True
    (outputs / "analysis" / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    rc, _ = _bundle(outputs, tmp_path)
    assert rc == 0
    assert "DIAGNOSTIC_ONLY" in capsys.readouterr().out


def test_every_bundled_file_hash_matches_disk(outputs, tmp_path):
    rc, _ = _bundle(outputs, tmp_path)
    assert rc == 0
    manifest = json.loads((outputs / "analysis" / "BUNDLE_MANIFEST.json").read_text())
    for entry in manifest["included_files"]:
        p = outputs / entry["path"]
        assert p.exists()
        assert wf.sha256_file(p) == entry["sha256"]
