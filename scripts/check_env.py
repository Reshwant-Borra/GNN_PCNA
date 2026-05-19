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

    print("PyTorch Geometric (required for model inference + training):")
    ok_pyg     = check("torch_geometric", min_version="2.4.0")
    check("torch_scatter")   # optional sparse kernel — speeds up some ops
    check("torch_sparse")    # optional sparse kernel
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

    print("Repo data:")
    n_pdb = len(list((REPO / "data" / "raw").glob("*.pdb")))
    n_pt  = len(list((REPO / "data" / "graphs").glob("*.pt")))
    manifest = REPO / "data" / "manifests" / "pdb_checksums.json"
    ckpt_v3f = REPO / "checkpoints" / "pcna" / "best_pcna_v3_fixed.ckpt"
    print(f"  {'[PASS]' if n_pdb >= 59 else '[FAIL]'}  PDB files              {n_pdb} in data/raw/  (need >=59)")
    print(f"  {'[PASS]' if n_pt  >= 80 else '[FAIL]'}  Graph tensors          {n_pt} in data/graphs/  (need >=80)")
    print(f"  {'[PASS]' if manifest.exists() else '[FAIL]'}  Checksum manifest      {'present' if manifest.exists() else 'MISSING'}")
    print(f"  {'[PASS]' if ckpt_v3f.exists() else '[FAIL]'}  Fixed checkpoint       {'present' if ckpt_v3f.exists() else 'MISSING'}")
    print()

    # Summary and fix instructions
    issues = []
    if not ok_torch:
        issues.append((
            "Install PyTorch",
            "pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu\n"
            "  (replace +cpu with +cu118 or +cu121 for NVIDIA GPU)"
        ))
    if not ok_pyg:
        issues.append((
            "Install PyTorch Geometric",
            "pip install torch-geometric\n"
            "  pip install torch-scatter torch-sparse \\\n"
            "    -f https://data.pyg.org/whl/torch-2.1.0+cpu.html\n"
            "  (replace +cpu with +cu118/+cu121 to match your torch build)"
        ))
    if not ok_numpy or not ok_scipy or not ok_bio or not ok_sklearn:
        issues.append((
            "Install remaining dependencies",
            "pip install -r requirements.txt"
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
        print("    python scripts/aoh_gate_check.py")
        print("    python scripts/run_test_eval.py")
        print("    streamlit run src/ui/app.py")
        print("=" * 55)

if __name__ == "__main__":
    main()
