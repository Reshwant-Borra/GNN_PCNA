"""
One-command data download and build pipeline for GNN-PCNA.

Downloads all 59 PCNA PDB files from RCSB, verifies SHA256 checksums,
builds PyG graph tensors, and optionally builds ESM2 features.

All raw files land in data/raw/ (committed to git).
Graph tensors land in data/graphs/ (also committed to git).

Usage
-----
    python scripts/download_data.py            # download + build graphs
    python scripts/download_data.py --verify   # checksum-verify only (no download)
    python scripts/download_data.py --skip-graphs  # download PDBs only
    python scripts/download_data.py --esm      # also build ESM2 features (slow, ~4GB)

After running:
    python scripts/make_split.py               # create train/val/test split
    python scripts/per_structure_analysis.py   # run per-structure analysis
    python scripts/full_eval.py                # full evaluation + figures

Requirements: requests, biopython, scipy, torch, torch-geometric
    See requirements.txt — pin with: pip install -r requirements.txt
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import requests

REPO = Path(__file__).parent.parent
RAW_DIR    = REPO / "data" / "raw"
GRAPH_DIR  = REPO / "data" / "graphs"
PCNA_DIR   = REPO / "data" / "pcna"
MANIFEST   = REPO / "data" / "manifests" / "pdb_checksums.json"
RCSB_URL   = "https://files.rcsb.org/download/{}.pdb"
RETRY_MAX  = 3
RETRY_WAIT = 2.0   # seconds between retries

# All 59 PCNA structures used in this project
# 1W61 is excluded — it is proline racemase, NOT PCNA
PCNA_STRUCTURES = [
    "9B8T", "6FCN", "4D2G", "3VKX", "3TBL", "9N3L", "1W60", "1U7B",
    "9CHM", "6EHT", "7EFA", "8GL9", "4RJF", "7KQ0", "8F5Q", "1UL1",
    "8UN0", "6CBI", "5YCO", "1AXC", "6K3A", "7NV0", "8GCJ", "5MAV",
    "6QC0", "5YD8", "8GLA", "6VVO", "2ZVL", "9EOA", "8UMU", "8COB",
    "6QCG", "6GIS", "8E84", "8UMY", "8UMT", "5MLO", "1VYJ", "3P87",
    "5MLW", "1VYM", "5MOM", "5E0T", "1U76", "6GWS", "6HVO", "6FCM",
    "2ZVM", "5E0V", "7M5N", "4ZTD", "9GY0", "8UI8", "8UI9", "5E0U",
    "2ZVK", "7M5L", "9CG4",
]

# PCNA positive control structures that also go into data/pcna/
PCNA_CORE = {"8GLA", "1W60", "1AXC"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def download_pdb(pdb_id: str, dest: Path) -> bool:
    url = RCSB_URL.format(pdb_id)
    for attempt in range(1, RETRY_MAX + 1):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and b"ATOM" in r.content:
                dest.write_bytes(r.content)
                return True
            print(f"    [{pdb_id}] HTTP {r.status_code} — attempt {attempt}/{RETRY_MAX}")
        except requests.RequestException as e:
            print(f"    [{pdb_id}] Error: {e} — attempt {attempt}/{RETRY_MAX}")
        if attempt < RETRY_MAX:
            time.sleep(RETRY_WAIT)
    return False


def build_graphs(pdb_ids: list[str]) -> None:
    """Build PyG graph tensors from downloaded PDB files."""
    sys.path.insert(0, str(REPO))
    try:
        from src.data_processing.parse_pdb import parse_pdb
        from src.data_processing.graph_construction import build_graph_v2
        import torch
    except ImportError as e:
        print(f"\n  [ERROR] Cannot import graph builder: {e}")
        print("  Install: pip install torch torch-geometric biopython scipy")
        return

    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    PCNA_DIR.mkdir(parents=True, exist_ok=True)

    ok = err = 0
    for pdb_id in pdb_ids:
        pdb_path = RAW_DIR / f"{pdb_id}.pdb"
        if not pdb_path.exists():
            print(f"  [SKIP] {pdb_id} — PDB not found")
            continue
        graph_path = GRAPH_DIR / f"{pdb_id}.pt"
        if graph_path.exists():
            print(f"  [SKIP] {pdb_id} — graph already exists")
            ok += 1
            continue
        try:
            residues = parse_pdb(pdb_path)
            data = build_graph_v2(residues)
            torch.save(data, graph_path)
            if pdb_id in PCNA_CORE:
                torch.save(data, PCNA_DIR / f"{pdb_id}.pt")
            print(f"  [OK]   {pdb_id} — {len(residues)} residues")
            ok += 1
        except Exception as e:
            print(f"  [ERR]  {pdb_id} — {e}")
            err += 1

    print(f"\n  Graphs built: {ok} ok, {err} errors")


def build_esm_features(pdb_ids: list[str]) -> None:
    """Build ESM2 t12 features (requires ~4 GB RAM, ~20 min)."""
    sys.path.insert(0, str(REPO))
    try:
        build_esm = REPO / "scripts" / "build_esm_features.py"
        if not build_esm.exists():
            print("  [SKIP] build_esm_features.py not found")
            return
        import subprocess
        for pdb_id in pdb_ids:
            print(f"  ESM2: {pdb_id}", end=" ... ", flush=True)
            result = subprocess.run(
                [sys.executable, str(build_esm), "--pdb", pdb_id],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print("OK")
            else:
                print(f"FAIL: {result.stderr[:60]}")
    except Exception as e:
        print(f"  [ERR] ESM build failed: {e}")


def save_manifest(checksums: dict[str, str]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(checksums, indent=2, sort_keys=True))
    print(f"\n  Manifest saved: {MANIFEST.relative_to(REPO)}")


def verify_manifest() -> tuple[int, int]:
    if not MANIFEST.exists():
        print("  No manifest found. Run without --verify first to create one.")
        return 0, 0
    checksums = json.loads(MANIFEST.read_text())
    ok = fail = 0
    for pdb_id, expected in checksums.items():
        path = RAW_DIR / f"{pdb_id}.pdb"
        if not path.exists():
            print(f"  [MISSING] {pdb_id}")
            fail += 1
            continue
        actual = sha256_file(path)
        if actual == expected:
            ok += 1
        else:
            print(f"  [CORRUPT] {pdb_id} — checksum mismatch")
            fail += 1
    print(f"\n  Verified: {ok} ok, {fail} missing/corrupt")
    return ok, fail


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download all GNN-PCNA data from RCSB and build graph tensors")
    parser.add_argument("--verify",      action="store_true",
                        help="Verify checksums of already-downloaded files (no download)")
    parser.add_argument("--skip-graphs", action="store_true",
                        help="Download PDB files only, skip graph construction")
    parser.add_argument("--esm",         action="store_true",
                        help="Also build ESM2 features (slow, ~20 min, requires ~4 GB RAM)")
    parser.add_argument("--force",       action="store_true",
                        help="Re-download even if file already exists")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    if args.verify:
        verify_manifest()
        return

    print("=" * 60)
    print("  GNN-PCNA Data Download + Build Pipeline")
    print("=" * 60)
    print(f"  Structures : {len(PCNA_STRUCTURES)}")
    print(f"  Destination: {RAW_DIR.relative_to(REPO)}")
    print()

    # ── Phase 1: Download PDB files ──────────────────────────────────────────
    print("Phase 1: Downloading PDB files from RCSB...")
    checksums: dict[str, str] = {}
    downloaded = skipped = failed = 0

    for pdb_id in PCNA_STRUCTURES:
        dest = RAW_DIR / f"{pdb_id}.pdb"
        if dest.exists() and not args.force:
            checksums[pdb_id] = sha256_file(dest)
            skipped += 1
            print(f"  [SKIP] {pdb_id} — already present")
            continue

        print(f"  [DL]   {pdb_id}", end=" ... ", flush=True)
        ok = download_pdb(pdb_id, dest)
        if ok:
            checksums[pdb_id] = sha256_file(dest)
            downloaded += 1
            print(f"OK ({dest.stat().st_size // 1024} KB)")
        else:
            failed += 1
            print("FAILED")
        time.sleep(0.1)   # polite delay

    save_manifest(checksums)
    print(f"\n  Downloaded: {downloaded}  Skipped: {skipped}  Failed: {failed}")

    if failed > 0:
        print(f"\n  [WARN] {failed} downloads failed. "
              f"Re-run with --force to retry, or check your internet connection.")

    if args.skip_graphs:
        print("\nSkipping graph construction (--skip-graphs). Run:")
        print("  python scripts/download_data.py  (without --skip-graphs)")
        return

    # ── Phase 2: Build graph tensors ─────────────────────────────────────────
    print("\nPhase 2: Building PyG graph tensors...")
    downloaded_ids = [p for p in PCNA_STRUCTURES
                      if (RAW_DIR / f"{p}.pdb").exists()]
    build_graphs(downloaded_ids)

    # ── Phase 3: ESM2 features (optional) ───────────────────────────────────
    if args.esm:
        print("\nPhase 3: Building ESM2 features (this will take ~20 min)...")
        build_esm_features(downloaded_ids)

    print("\n" + "=" * 60)
    print("  Done. Next steps:")
    print("  1. python scripts/make_split.py")
    print("  2. python -m src.training.train  (optional — checkpoints included)")
    print("  3. python scripts/per_structure_analysis.py")
    print("  4. python scripts/full_eval.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
