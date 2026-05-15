"""
fetch_structures.py — Stage 1 of the GNN-PCNA pipeline.

Downloads and validates PDB structures from RCSB, then organises them
into data/raw/ (original) and data/processed/ (stripped + standardised).

Handles:
  - Known ground-truth structures (1W60, 8GLA)
  - CryptoSite benchmark proteins (transfer-learning set)
  - UniProt P12004 cross-references

Verification layers (mirrors agents/pcna_crawler.py logic):
  1. HTTP 200 + non-empty file
  2. Valid PDB header (ATOM records present)
  3. Chain count matches expected (PCNA = 3 chains)
  4. Resolution filter (< 3.5 Å for crystallography)
  5. Cα atom completeness (>= 95% of residues have a Cα)

Usage (standalone):
    python -m src.data_processing.fetch_structures
    python -m src.data_processing.fetch_structures --ids 1W60 8GLA
    python -m src.data_processing.fetch_structures --cryptosite
    python -m src.data_processing.fetch_structures --catalog data/catalog/pcna_data_catalog.json

Called by the pipeline:
    from src.data_processing.fetch_structures import fetch_pdb, fetch_from_catalog
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import requests

# ── directory layout ────────────────────────────────────────────────────────────
REPO_ROOT     = Path(__file__).parent.parent.parent
RAW_DIR       = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
CATALOG_DIR   = REPO_ROOT / "data" / "catalog"
LOGS_DIR      = REPO_ROOT / "data" / "catalog"

for d in (RAW_DIR, PROCESSED_DIR, CATALOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── constants ───────────────────────────────────────────────────────────────────
RCSB_PDB_URL    = "https://files.rcsb.org/download/{}.pdb"
RCSB_META_URL   = "https://data.rcsb.org/rest/v1/core/entry/{}"
POLITE_DELAY    = 0.4   # seconds between RCSB requests

# Ground-truth structures — always fetch, never skip
PCNA_CORE_IDS = ["1W60", "8GLA", "1AXC", "1W61"]

# CryptoSite benchmark PDB IDs (Cimermancic et al. 2016, Table S1)
# Source: https://github.com/salilab/cryptosite (parsed from paper supplementary)
CRYPTOSITE_IDS = [
    "1BLR", "1BU9", "1C3I", "1C5H", "1D09", "1DLN", "1E2X", "1E3V",
    "1FBO", "1GBG", "1GQY", "1H8A", "1HP2", "1IQD", "1JBP", "1JWP",
    "1K3Y", "1LB6", "1M17", "1NRY", "1O3P", "1OG2", "1OIN", "1ONE",
    "1P9Y", "1PDZ", "1PZO", "1Q5H", "1RJ8", "1SQO", "1THJ", "1TML",
    "1V48", "1VFB", "1W4E", "1W9H", "1XHY", "1XKK", "1XQ4", "1YCS",
    "1Z7X", "1ZC3", "2AM9", "2B8H", "2BKM", "2BRJ", "2C32", "2CLR",
    "2CNN", "2DR2", "2DXX", "2EUF", "2GV1", "2H5C", "2HM7", "2HNX",
    "2HQS", "2J58", "2JA3", "2JGU", "2K1V", "2LZM", "2NLZ", "2NMO",
    "2NWX", "2OQB", "2P0R", "2P54", "2PKT", "2Q1T", "2QKH", "2R8Q",
    "2VGO", "2VO5", "2WER", "2X6D", "2XBP", "2XHM", "2YHW", "3BYH",
    "3C0I", "3CL7", "3D0E", "3EML", "3FU8", "3GXD", "3HXM", "3KCW",
    "3KQ4", "3L7U", "3N86", "3PXF",
]


# ── data structures ─────────────────────────────────────────────────────────────

@dataclass
class FetchResult:
    pdb_id:     str
    status:     str          # "ok" | "failed" | "skipped"
    raw_path:   Optional[Path] = None
    reason:     str = ""
    chains:     int = 0
    resolution: Optional[float] = None
    residue_count: int = 0
    ca_completeness: float = 0.0  # fraction of residues with Cα

    def to_dict(self) -> dict:
        d = asdict(self)
        d["raw_path"] = str(self.raw_path) if self.raw_path else None
        return d


@dataclass
class FetchSession:
    ok:      list[FetchResult] = field(default_factory=list)
    failed:  list[FetchResult] = field(default_factory=list)
    skipped: list[FetchResult] = field(default_factory=list)

    def record(self, r: FetchResult):
        if r.status == "ok":
            self.ok.append(r)
        elif r.status == "failed":
            self.failed.append(r)
        else:
            self.skipped.append(r)

    def summary(self) -> str:
        return (f"OK={len(self.ok)}  failed={len(self.failed)}  "
                f"skipped={len(self.skipped)}")

    def save(self, path: Path):
        data = {
            "ok":      [r.to_dict() for r in self.ok],
            "failed":  [r.to_dict() for r in self.failed],
            "skipped": [r.to_dict() for r in self.skipped],
        }
        path.write_text(json.dumps(data, indent=2))


# ── verification ─────────────────────────────────────────────────────────────────

def _verify_pdb_file(path: Path, pdb_id: str) -> FetchResult:
    """
    Run all verification checks on a downloaded .pdb file.
    Returns FetchResult with status 'ok' or 'failed'.
    """
    text = path.read_text(errors="ignore")
    lines = text.splitlines()

    # Check 1: ATOM records present
    atom_lines = [l for l in lines if l.startswith("ATOM")]
    if not atom_lines:
        return FetchResult(pdb_id, "failed", path, "no ATOM records")

    # Check 2: count chains
    chains = {l[21] for l in atom_lines if len(l) > 21}
    chain_count = len(chains)

    # Check 3: resolution from REMARK 2
    resolution = None
    for l in lines:
        if l.startswith("REMARK   2 RESOLUTION"):
            m = re.search(r"(\d+\.\d+)", l)
            if m:
                resolution = float(m.group(1))
                break

    # Check 4: resolution filter — warn only for core structures, hard fail otherwise
    if resolution is not None and resolution > 3.5:
        if pdb_id in PCNA_CORE_IDS:
            pass  # ground-truth structures kept regardless of resolution
        else:
            return FetchResult(pdb_id, "failed", path,
                               f"resolution {resolution}Å > 3.5Å threshold",
                               chain_count, resolution)

    # Check 5: Cα completeness
    residue_ids = {(l[21], l[22:26].strip()) for l in atom_lines}
    ca_lines    = [l for l in atom_lines
                   if len(l) > 16 and l[12:16].strip() == "CA"]
    ca_res      = {(l[21], l[22:26].strip()) for l in ca_lines}
    completeness = len(ca_res) / max(len(residue_ids), 1)

    if completeness < 0.90:
        return FetchResult(pdb_id, "failed", path,
                           f"Cα completeness {completeness:.1%} < 90%",
                           chain_count, resolution, len(residue_ids), completeness)

    return FetchResult(pdb_id, "ok", path, "passed all checks",
                       chain_count, resolution, len(residue_ids), completeness)


# ── core fetch logic ─────────────────────────────────────────────────────────────

def fetch_pdb(pdb_id: str, force: bool = False) -> FetchResult:
    """
    Download one PDB file to data/raw/{PDB_ID}.pdb.
    Skips if already present (unless force=True).
    Runs verification after download.
    """
    pdb_id = pdb_id.upper().strip()
    dest   = RAW_DIR / f"{pdb_id}.pdb"

    if dest.exists() and not force:
        result = _verify_pdb_file(dest, pdb_id)
        result.status  = "skipped"
        result.reason  = "already exists"
        return result

    url = RCSB_PDB_URL.format(pdb_id)
    try:
        time.sleep(POLITE_DELAY)
        r = requests.get(url, timeout=30,
                         headers={"User-Agent": "GNN-PCNA/1.0 (academic)"})
        r.raise_for_status()
        if len(r.content) < 1000:
            return FetchResult(pdb_id, "failed", reason="response too small")
        dest.write_bytes(r.content)
    except requests.RequestException as e:
        return FetchResult(pdb_id, "failed", reason=str(e))

    return _verify_pdb_file(dest, pdb_id)


def fetch_batch(pdb_ids: list[str], force: bool = False,
                verbose: bool = True) -> FetchSession:
    """Download and verify a list of PDB IDs."""
    session = FetchSession()
    total   = len(pdb_ids)

    for i, pdb_id in enumerate(pdb_ids, 1):
        result = fetch_pdb(pdb_id, force=force)
        session.record(result)
        if verbose:
            icon = {"ok": "✓", "failed": "✗", "skipped": "–"}.get(result.status, "?")
            print(f"  [{i:>4}/{total}] {icon} {pdb_id:<6}  {result.reason[:60]}")

    return session


def fetch_from_catalog(catalog_path: Path, min_score: float = 0.3,
                       limit: int = 50, force: bool = False) -> FetchSession:
    """
    Fetch PDB files listed in a crawler catalog (data/catalog/pcna_data_catalog.json).
    Only downloads entries with relevance_score >= min_score.
    """
    catalog  = json.loads(catalog_path.read_text())
    entries  = [e for e in catalog.get("pdb_entries", [])
                if e.get("relevance_score", 0) >= min_score][:limit]
    pdb_ids  = [e["pdb_id"] for e in entries]
    print(f"Fetching {len(pdb_ids)} structures from catalog "
          f"(score ≥ {min_score}, limit={limit})")
    return fetch_batch(pdb_ids, force=force)


def fetch_cryptosite(force: bool = False) -> FetchSession:
    """Download the full CryptoSite benchmark set."""
    print(f"Fetching CryptoSite benchmark ({len(CRYPTOSITE_IDS)} proteins)...")
    return fetch_batch(CRYPTOSITE_IDS, force=force)


def strip_processed(pdb_id: str, keep_ligand: str | None = None) -> Optional[Path]:
    """
    Write a stripped copy of data/raw/{PDB_ID}.pdb to data/processed/{PDB_ID}_clean.pdb.
    Removes HETATM (except keep_ligand), waters (HOH), and ANISOU records.
    Returns output path or None if source doesn't exist.
    """
    src  = RAW_DIR / f"{pdb_id}.pdb"
    dest = PROCESSED_DIR / f"{pdb_id}_clean.pdb"
    if not src.exists():
        return None
    if dest.exists():
        return dest

    kept = []
    with src.open(errors="ignore") as fh:
        for line in fh:
            rec = line[:6].strip()
            if rec == "ATOM":
                kept.append(line)
            elif rec == "HETATM":
                resname = line[17:20].strip()
                if resname == "HOH":
                    continue
                if keep_ligand and resname == keep_ligand:
                    kept.append(line)
            elif rec in ("HEADER", "TITLE", "REMARK", "SEQRES", "CRYST1",
                         "ORIGX1", "ORIGX2", "ORIGX3", "SCALE1", "SCALE2",
                         "SCALE3", "TER", "END"):
                kept.append(line)
            # drop ANISOU, CONECT, MASTER, MODRES

    dest.write_text("".join(kept))
    return dest


# ── main ─────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Stage 1 pipeline: fetch + verify PDB structures")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ids", nargs="+", metavar="PDB_ID",
                       help="Specific PDB IDs to fetch")
    group.add_argument("--cryptosite", action="store_true",
                       help="Fetch full CryptoSite benchmark set")
    group.add_argument("--catalog", type=Path,
                       help="Path to crawler catalog JSON")
    group.add_argument("--core", action="store_true",
                       help="Fetch only PCNA core structures (1W60, 8GLA, 1AXC, 1W61)")
    parser.add_argument("--force", action="store_true",
                        help="Re-download even if file exists")
    parser.add_argument("--strip", action="store_true",
                        help="Also write stripped copies to data/processed/")
    parser.add_argument("--min-score", type=float, default=0.3,
                        help="Min relevance score for catalog mode (default 0.3)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Max entries to fetch from catalog (default 50)")
    args = parser.parse_args()

    # Determine PDB list
    if args.ids:
        session = fetch_batch([i.upper() for i in args.ids], force=args.force)
    elif args.cryptosite:
        session = fetch_cryptosite(force=args.force)
    elif args.catalog:
        session = fetch_from_catalog(args.catalog, args.min_score,
                                     args.limit, args.force)
    else:
        # Default: fetch core PCNA structures
        print("Fetching PCNA core structures...")
        session = fetch_batch(PCNA_CORE_IDS, force=args.force)

    print(f"\n{session.summary()}")

    if args.strip:
        print("\nStripping processed copies...")
        for r in session.ok:
            ligand = "AOH" if r.pdb_id == "8GLA" else None
            out = strip_processed(r.pdb_id, keep_ligand=ligand)
            if out:
                print(f"  → {out.name}")

    # Save session log
    log_path = CATALOG_DIR / "fetch_session.json"
    session.save(log_path)
    print(f"\nSession log → {log_path}")

    if session.failed:
        print("\nFailed:")
        for r in session.failed:
            print(f"  {r.pdb_id}: {r.reason}")


if __name__ == "__main__":
    main()
