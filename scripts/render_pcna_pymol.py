"""
Render PCNA pocket figures via PyMOL.

Downloads 1W60 and 8GLA from RCSB if not already in data/raw/, then
invokes PyMOL in headless mode (-c) on each .pml script.

Usage:
    python scripts/render_pcna_pymol.py
    python scripts/render_pcna_pymol.py --only 1w60   # single structure
    python scripts/render_pcna_pymol.py --pymol /path/to/pymol
    python scripts/render_pcna_pymol.py --interactive  # open PyMOL GUI

Requirements:
    - PyMOL (open-source or incentive) in PATH, or --pymol flag
    - Internet access for first run (PDB download)

Outputs:
    reports/figures/pcna_aoh1996_pocket_highlight.png   (1W60 apo)
    reports/figures/pcna_8gla_holo_pocket.png           (8GLA holo)
"""
from __future__ import annotations
import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW  = REPO / "data" / "raw"
PML  = REPO / "scripts" / "pymol"
OUT  = REPO / "reports" / "figures"

STRUCTURES = {
    "1w60": {
        "pdb_id": "1W60",
        "script": PML / "pcna_1w60_aoh_pocket.py",
        "out":    OUT / "pcna_aoh1996_pocket_highlight.png",
    },
    "8gla": {
        "pdb_id": "8GLA",
        "script": PML / "pcna_8gla_holo_pocket.py",
        "out":    OUT / "pcna_8gla_holo_pocket.png",
    },
}

RCSB_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"


def _find_pymol(hint: str | None) -> str:
    """Return path to pymol executable or raise."""
    candidates = []
    if hint:
        candidates.append(hint)
    candidates += ["pymol", "PyMOL", "pymol3"]
    # Common Windows install paths
    import os as _os
    _home = _os.path.expanduser("~")
    candidates += [
        rf"{_home}\miniconda3\Scripts\pymol.exe",
        rf"{_home}\anaconda3\Scripts\pymol.exe",
        rf"C:\ProgramData\miniconda3\Scripts\pymol.exe",
        rf"C:\ProgramData\anaconda3\Scripts\pymol.exe",
    ]
    for ver in ["3.0", "2.6", "2.5"]:
        candidates += [
            rf"C:\Program Files\PyMOL\PyMOL {ver}\PyMOLWin.exe",
            rf"C:\Program Files (x86)\PyMOL\PyMOL {ver}\PyMOLWin.exe",
        ]
    for c in candidates:
        found = shutil.which(c) or (Path(c).exists() and c)
        if found:
            return str(found)
    raise FileNotFoundError(
        "PyMOL not found in PATH.\n"
        "  Install via: conda install -c conda-forge pymol-open-source\n"
        "  Or pass --pymol /path/to/pymol"
    )


def _fetch_pdb(pdb_id: str) -> Path:
    """Download PDB from RCSB if not already cached."""
    dest = RAW / f"{pdb_id}.pdb"
    if dest.exists():
        print(f"  [cache] {pdb_id}.pdb already in data/raw/")
        return dest
    url = RCSB_URL.format(pdb_id=pdb_id)
    print(f"  [fetch] {url}")
    RAW.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  [ok]    {dest.stat().st_size // 1024} KB")
    except Exception as e:
        print(f"  [warn]  Download failed ({e}); PyMOL will fetch inline.")
    return dest


def _run_pymol(pymol_bin: str, script: Path, out_png: Path, interactive: bool) -> int:
    """Invoke PyMOL on a .py script, injecting absolute paths via env vars."""
    import os
    env = os.environ.copy()
    env["PYMOL_OUT_PNG"]   = str(out_png.resolve())
    env["PYMOL_REPO_ROOT"] = str(REPO.resolve())
    flags = [] if interactive else ["-c"]
    cmd = [pymol_bin] + flags + [str(script.resolve())]
    print(f"\n  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only",        choices=["1w60", "8gla"],
                        help="Render only one structure")
    parser.add_argument("--pymol",       default=None,
                        help="Path to PyMOL executable")
    parser.add_argument("--interactive", action="store_true",
                        help="Open PyMOL GUI instead of headless mode")
    parser.add_argument("--skip-fetch",  action="store_true",
                        help="Skip PDB download (assume already in data/raw/)")
    args = parser.parse_args()

    try:
        pymol_bin = _find_pymol(args.pymol)
        print(f"[pymol] {pymol_bin}")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    OUT.mkdir(parents=True, exist_ok=True)

    targets = [args.only] if args.only else list(STRUCTURES.keys())
    failures = []

    for key in targets:
        info = STRUCTURES[key]
        print(f"\n{'='*60}")
        print(f"  Rendering {info['pdb_id']} -> {info['out'].name}")
        print(f"{'='*60}")

        if not args.skip_fetch:
            _fetch_pdb(info["pdb_id"])

        rc = _run_pymol(pymol_bin, info["script"], info["out"], args.interactive)
        if rc != 0:
            print(f"  [warn] PyMOL exited with code {rc}")
            failures.append(info["pdb_id"])
        elif info["out"].exists():
            kb = info["out"].stat().st_size // 1024
            print(f"  [ok]   {info['out']} ({kb} KB)")
        else:
            print(f"  [warn] Output PNG not found at {info['out']}")
            failures.append(info["pdb_id"])

    print()
    if failures:
        print(f"[WARN] Failed: {', '.join(failures)}")
        sys.exit(1)
    else:
        print(f"[DONE] All figures saved to {OUT}/")


if __name__ == "__main__":
    main()
