"""
Environment checker for GNN-PCNA.

Run this first before anything else to verify your setup is correct.

    python scripts/check_env.py

Prints a table of all required packages with versions, and tells you
exactly what to install if anything is missing.
"""
from __future__ import annotations
import sys
import importlib
import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent
PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

def check(name: str, import_name: str | None = None, min_version: str | None = None) -> bool:
    mod_name = import_name or name
    try:
        mod = importlib.import_module(mod_name)
        ver = getattr(mod, "__version__", "?")
        status = PASS
        if min_version:
            from packaging.version import Version
            try:
                ok = Version(ver) >= Version(min_version)
                status = PASS if ok else WARN
            except Exception:
                pass
        print(f"  {status}  {name:<22} {ver}")
        return True
    except ImportError:
        print(f"  {FAIL}  {name:<22} NOT INSTALLED")
        return False

def main():
    print("=" * 55)
    print("  GNN-PCNA Environment Check")
    print("=" * 55)
    print(f"  Python {sys.version.split()[0]}  ({sys.executable})")
    print()

    print("Core (required for all scripts):")
    ok_torch  = check("torch",        min_version="2.1.0")
    ok_numpy  = check("numpy",        min_version="1.24.0")
    ok_scipy  = check("scipy",        min_version="1.11.0")
    ok_bio    = check("biopython",    "Bio",        min_version="1.81")
    ok_sklearn= check("scikit-learn", "sklearn",    min_version="1.3.0")
    print()

    print("PyTorch Geometric (required for all ML training/evaluation commands):")
    ok_pyg     = check("torch_geometric", min_version="2.4.0")
    ok_scatter = check("torch_scatter")
    ok_sparse  = check("torch_sparse")
    print()

    print("UI and reporting:")
    check("streamlit",   min_version="1.35.0")
    check("matplotlib",  min_version="3.7.0")
    check("pandas",      min_version="2.0.0")
    check("tqdm")
    check("requests")
    check("bs4")
    print()

    print("Optional:")
    check("esm",         "esm")
    check("MDAnalysis",  "MDAnalysis")
    check("prody",       "prody")
    print()

    print("MD stack:")
    ok_openmm = check("openmm")
    check("mdtraj")
    check("pdbfixer")
    check("gemmi")
    if ok_openmm:
        try:
            import openmm as mm
            platforms = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
            gpu_requested = "--gpu" in sys.argv or "--cuda" in sys.argv
            status = PASS if (not gpu_requested or "CUDA" in platforms) else FAIL
            print(f"  {status}  OpenMM platforms      {platforms}")
        except Exception as exc:
            print(f"  {WARN}  OpenMM platforms      unavailable: {exc}")
    print(f"  {PASS if shutil.which('tmux') else WARN}  tmux                  "
          f"{shutil.which('tmux') or 'not installed; required by md.sh launchers'}")
    print()

    print("Current repository artifacts:")
    n_pdb = len(list((REPO / "data" / "raw").glob("*.pdb")))
    n_graph_xl = len(list((REPO / "data" / "graphs_xl").glob("*.pt")))
    gnn_registry = REPO / "artifacts" / "provenance" / "AUGUST_THREE_SEED_CHECKPOINT_REGISTRY.json"
    graph_manifest = REPO / "artifacts" / "provenance" / "GRAPH_LINEAGE_520_MANIFEST.json"
    handoff = REPO / "md_validation_4070" / "pockets" / "final_consensus_1w60_20260815.json"
    protocol = REPO / "md_validation_4070" / "FROZEN_MD_ANALYSIS_PROTOCOL.json"
    mdsh = REPO / "md.sh"
    expected_ckpts = [
        REPO / "artifacts" / "go_prep" / f"seed_{seed}" / "best.ckpt"
        for seed in (42, 43, 44)
    ]
    print(f"  {PASS if n_pdb >= 7 else FAIL}  PCNA raw PDBs          {n_pdb} in data/raw/")
    print(f"  {PASS if all(p.exists() for p in expected_ckpts) else FAIL}  Frozen checkpoints    "
          f"{sum(p.exists() for p in expected_ckpts)}/3 present")
    print(f"  {PASS if gnn_registry.exists() else FAIL}  Checkpoint registry  "
          f"{'present' if gnn_registry.exists() else 'MISSING'}")
    print(f"  {PASS if handoff.exists() else FAIL}  Frozen handoff       "
          f"{'present' if handoff.exists() else 'MISSING'}")
    print(f"  {PASS if protocol.exists() else FAIL}  Frozen MD protocol   "
          f"{'present' if protocol.exists() else 'MISSING'}")
    print(f"  {PASS if mdsh.exists() else FAIL}  Canonical launcher   "
          f"{'present' if mdsh.exists() else 'MISSING'}")
    print(f"  {PASS if graph_manifest.exists() else FAIL}  Graph lineage       "
          f"{'present' if graph_manifest.exists() else 'MISSING'}")
    print(f"  {PASS if n_graph_xl >= 55 else WARN}  Local 520-dim graphs  "
          f"{n_graph_xl} in data/graphs_xl/ (55 required for full split validation)")
    if graph_manifest.exists():
        proc = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "verify_graph_lineage.py"), "--allow-missing"],
            cwd=REPO, text=True, capture_output=True, timeout=120,
        )
        status = PASS if proc.returncode == 0 else WARN
        print(f"  {status}  Graph lineage check   "
              f"{'available/retrievable' if proc.returncode == 0 else 'see verify_graph_lineage.py'}")
    print()

    # Summary and fix instructions
    issues = []
    if not ok_torch:
        issues.append((
            "Install PyTorch",
            "pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu\n"
            "  (replace +cpu with +cu118 or +cu121 for NVIDIA GPU)"
        ))
    if not ok_pyg or not ok_scatter or not ok_sparse:
        issues.append((
            "Install PyTorch Geometric and sparse kernels",
            "pip install torch-geometric\n"
            "  pip install torch-scatter torch-sparse \\\n"
            "    -f https://data.pyg.org/whl/torch-2.1.0+cpu.html\n"
            "  (replace +cpu with +cu118/+cu121 to match your torch build)"
        ))
    if not ok_numpy or not ok_scipy or not ok_bio or not ok_sklearn:
        issues.append((
            "Install remaining dependencies",
            "pip install numpy scipy biopython scikit-learn pandas matplotlib requests beautifulsoup4"
        ))
    if not ok_openmm:
        issues.append((
            "Install the MD environment",
            "conda env create -f md_validation_4070/environment.yml && conda activate pcna-md-4070"
        ))

    if issues:
        print("=" * 55)
        print("  ACTION REQUIRED — fix in order:")
        print("=" * 55)
        for i, (title, cmd) in enumerate(issues, 1):
            print(f"\n  {i}. {title}")
            print(f"     {cmd}")
        print()
        sys.exit(1)
    else:
        print("=" * 55)
        print("  All checks passed. Ready to run:")
        print("    python3 scripts/verify_graph_lineage.py --retrieve-from-origin")
        print("    python3 -m pytest -q")
        print("    ./md.sh smoke")
        print("=" * 55)

if __name__ == "__main__":
    main()
