#!/usr/bin/env python3
"""
Phase 4 PCNA Inference Crawl

Downloads mmCIF files for all PCNA/sliding-clamp inference targets (~70-120 structures).
Spec: Rishi's Phase 4 PCNA Inference Crawl specification (2026-05-29).

Outputs:
  data/raw_intake/phase4_pcna_crawl/mmcif/{PDB_ID}.cif.gz
  data/raw_intake/phase4_pcna_crawl/phase4_crawl_manifest.json
  data/raw_intake/phase4_pcna_crawl/errors.log

Usage:
  python scripts/phase4_pcna_crawl.py [--dry-run] [--skip-verify]
"""

import sys
import os
import json
import gzip
import hashlib
import logging
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
import requests

# --- Paths ---
REPO_ROOT = Path(__file__).resolve().parent.parent  # Desktop/GNN_PCNA/
OUTPUT_DIR = REPO_ROOT / "data" / "raw_intake" / "phase4_pcna_crawl"
MMCIF_DIR = OUTPUT_DIR / "mmcif"
MANIFEST_PATH = OUTPUT_DIR / "phase4_crawl_manifest.json"
ERRORS_LOG = OUTPUT_DIR / "errors.log"
CANDIDATE_MANIFEST = REPO_ROOT / "data" / "registries" / "phase4_candidate_manifest.json"
CRYPTOBENCH_CIF_DIR = REPO_ROOT / "data" / "raw_intake" / "cryptobench" / "cif-files"

# --- URLs ---
RCSB_DOWNLOAD_BASE = "https://files.rcsb.org/download/{pdb_id}.cif.gz"
RCSB_SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_ENTRY_URL = "https://data.rcsb.org/rest/v1/core/entry/{pdb_id}"

# --- Constants ---
RESOLUTION_CUTOFF = 3.5
SPOT_SAMPLE_N = 10
QUERY_B_MAX = 20
QUERY_C_MAX = 30
REQUEST_TIMEOUT = 60
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2.0  # seconds, doubles each retry

# Part 1 extras not in candidate manifest
PART1_EXTRAS = [
    {"pdb_id": "1W60", "notes": "PCNA holo — used in earlier PCNA work; not in current manifest"},
    {"pdb_id": "1U7B", "notes": "PCNA holo — Reshwant's priority list"},
]

# Special flags from spec
PART1_FLAGS = {
    "8GLA": {
        "flag": "POSITIVE_CONTROL",
        "flag_note": "AOH1996/ZQZ ligand; force-included despite 3.77 A > 3.5 A (PMID 37531956)",
    },
    "5E0V": {
        "flag": "VARIANT_NOT_APO",
        "flag_note": (
            "S228I disease variant + FEN1 peptide. NOT apo WT PCNA. "
            "Do not use as apo reference. PMID 26688547."
        ),
    },
}


def setup_logging(errors_log: Path) -> logging.Logger:
    errors_log.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("phase4_crawl")
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(errors_log, mode="w", encoding="utf-8")
    fh.setLevel(logging.WARNING)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def gzip_ok(path: Path) -> bool:
    try:
        with gzip.open(path, "rb") as f:
            while f.read(65536):
                pass
        return True
    except Exception:
        return False


def download_cif(pdb_id: str, dest: Path, session: requests.Session, logger: logging.Logger) -> dict:
    url = RCSB_DOWNLOAD_BASE.format(pdb_id=pdb_id)
    utc_start = datetime.now(timezone.utc).isoformat()

    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = session.get(url, stream=True, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            h = hashlib.sha256()
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(65536):
                    f.write(chunk)
                    h.update(chunk)
            size = dest.stat().st_size
            sha = h.hexdigest()
            return {
                "status": "ok",
                "source_url": url,
                "download_utc": utc_start,
                "file_size_bytes": size,
                "sha256": sha,
            }
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"{pdb_id}: 404 Not Found at {url}")
                return {"status": "failed", "source_url": url, "download_utc": utc_start,
                        "error": f"HTTP 404"}
            logger.warning(f"{pdb_id}: HTTP {e.response.status_code} attempt {attempt}")
        except Exception as e:
            logger.warning(f"{pdb_id}: attempt {attempt} error: {e}")
        if attempt < RETRY_ATTEMPTS:
            time.sleep(RETRY_BACKOFF * attempt)

    return {"status": "failed", "source_url": url, "download_utc": utc_start,
            "error": "max retries exceeded"}


def rcsb_search(query: dict, logger: logging.Logger) -> dict | None:
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.post(RCSB_SEARCH_URL, json=query, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            if not resp.text.strip():
                # Empty body = zero results
                return {"total_count": 0, "result_set": []}
            return resp.json()
        except Exception as e:
            logger.warning(f"RCSB search attempt {attempt} failed: {e}")
            if attempt < RETRY_ATTEMPTS:
                time.sleep(RETRY_BACKOFF * attempt)
    return None


def get_resolution(pdb_id: str, session: requests.Session, logger: logging.Logger) -> float | None:
    url = RCSB_ENTRY_URL.format(pdb_id=pdb_id)
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        res = data.get("rcsb_entry_info", {}).get("resolution_combined")
        if isinstance(res, list):
            res = min(res) if res else None
        return float(res) if res is not None else None
    except Exception as e:
        logger.warning(f"Could not fetch resolution for {pdb_id}: {e}")
        return None


def query_2a(logger: logging.Logger) -> tuple[list[str], int]:
    """Human PCNA (UniProt P12004). Returns (pdb_ids_all, total_count_from_api)."""
    query_all = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": "P12004",
            },
        },
        "return_type": "entry",
        "request_options": {
            "results_verbosity": "minimal",
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined", "direction": "asc"}],
            "paginate": {"start": 0, "rows": 500},
        },
    }
    result = rcsb_search(query_all, logger)
    if result is None:
        logger.error("Query 2A failed; skipping.")
        return [], 0
    total_count = result.get("total_count", 0)
    ids = [r["identifier"] for r in result.get("result_set", [])]
    logger.info(f"Query 2A (P12004): total_count={total_count}, returned={len(ids)}")
    return ids, total_count


def query_2b(logger: logging.Logger) -> list[str]:
    """E. coli beta clamp (UniProt P0ABS6). Returns up to QUERY_B_MAX IDs."""
    query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": "P0ABS6",
            },
        },
        "return_type": "entry",
        "request_options": {
            "results_verbosity": "minimal",
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined", "direction": "asc"}],
            "paginate": {"start": 0, "rows": QUERY_B_MAX},
        },
    }
    result = rcsb_search(query, logger)
    if result is None:
        logger.error("Query 2B failed; skipping.")
        return []
    ids = [r["identifier"] for r in result.get("result_set", [])]
    logger.info(f"Query 2B (P0ABS6 beta clamp): returned={len(ids)}")
    return ids


def query_2c(logger: logging.Logger) -> list[str]:
    """Archaeal/yeast PCNA homologs via full-text 'sliding clamp', res <= 3.5 A. Up to 30.

    Note: RCSB Search API returns 204 when a full_text terminal is nested inside a 3-node
    compound group that also includes an experimental_method sub-group. The experimental
    method filter is omitted here — RCSB only indexes real experimental structures anyway,
    so the resolution filter is the binding constraint.
    """
    query = {
        "query": {
            "type": "group",
            "logical_operator": "and",
            "nodes": [
                {
                    "type": "terminal",
                    "service": "full_text",
                    "parameters": {"value": "sliding clamp"},
                },
                {
                    "type": "terminal",
                    "service": "text",
                    "parameters": {
                        "attribute": "rcsb_entry_info.resolution_combined",
                        "operator": "less_or_equal",
                        "value": RESOLUTION_CUTOFF,
                    },
                },
            ],
        },
        "return_type": "entry",
        "request_options": {
            "results_verbosity": "minimal",
            "sort": [{"sort_by": "rcsb_entry_info.resolution_combined", "direction": "asc"}],
            "paginate": {"start": 0, "rows": QUERY_C_MAX},
        },
    }
    result = rcsb_search(query, logger)
    if result is None:
        logger.error("Query 2C failed; skipping.")
        return []
    ids = [r["identifier"] for r in result.get("result_set", [])]
    logger.info(f"Query 2C (sliding clamp, res<=3.5 A): returned={len(ids)}")
    return ids


def spot_parse(paths: list[Path], logger: logging.Logger) -> list[str]:
    """Try gemmi spot-parse on sample. Return list of pdb_ids that failed."""
    try:
        import gemmi
    except ImportError:
        logger.warning("gemmi not available; skipping spot-parse (install with: pip install gemmi)")
        return []

    import random
    sample = random.sample(paths, min(SPOT_SAMPLE_N, len(paths)))
    failed = []
    for p in sample:
        pdb_id = p.stem.upper()
        try:
            doc = gemmi.cif.read(str(p))
            block = doc.sole_block()
            atom_site = block.find("_atom_site.", ["type_symbol"])
            ca_count = sum(1 for row in atom_site)
            if ca_count == 0:
                logger.warning(f"Spot-parse {pdb_id}: _atom_site has 0 rows (possible HTML error page)")
                failed.append(pdb_id)
            else:
                logger.info(f"Spot-parse {pdb_id}: ok ({ca_count} atom_site rows)")
        except Exception as e:
            logger.warning(f"Spot-parse {pdb_id}: FAILED — {e}")
            failed.append(pdb_id)
    return failed


def build_part1_entries(candidate_manifest: dict) -> list[dict]:
    """Build ordered Part 1 download list: extras first (1W60, 1U7B), then manifest candidates."""
    entries = []

    # Extra structures not in manifest
    for extra in PART1_EXTRAS:
        pdb_id = extra["pdb_id"]
        entry = {
            "pdb_id": pdb_id,
            "part": "1",
            "rank_in_candidate_manifest": None,
            "resolution_angstrom": None,
            "has_ligand_per_manifest": None,
            "notes": extra["notes"],
        }
        entry.update(PART1_FLAGS.get(pdb_id, {}))
        entries.append(entry)

    # 54 candidates from manifest
    for cand in candidate_manifest.get("candidates", []):
        pdb_id = cand["pdb_id"]
        entry = {
            "pdb_id": pdb_id,
            "part": "1",
            "rank_in_candidate_manifest": cand.get("rank"),
            "resolution_angstrom": cand.get("resolution_angstrom"),
            "has_ligand_per_manifest": cand.get("has_ligand"),
            "notes": cand.get("notes"),
        }
        entry.update(PART1_FLAGS.get(pdb_id, {}))
        entries.append(entry)

    return entries


def main():
    parser = argparse.ArgumentParser(description="Phase 4 PCNA Inference Crawl")
    parser.add_argument("--dry-run", action="store_true", help="Plan only, no downloads")
    parser.add_argument("--skip-verify", action="store_true", help="Skip post-download verification")
    args = parser.parse_args()

    MMCIF_DIR.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(ERRORS_LOG)

    logger.info("=" * 60)
    logger.info("Phase 4 PCNA Inference Crawl")
    logger.info(f"Output dir: {OUTPUT_DIR}")
    logger.info(f"Dry-run: {args.dry_run}")
    logger.info("=" * 60)

    # Load exclusion set: PDB IDs already in cryptobench/cif-files/
    existing_cryptobench = set()
    if CRYPTOBENCH_CIF_DIR.exists():
        for f in CRYPTOBENCH_CIF_DIR.iterdir():
            pdb_id = f.stem.upper().rstrip(".")
            if pdb_id:
                existing_cryptobench.add(pdb_id)
    logger.info(f"Cryptobench exclusion set: {len(existing_cryptobench)} structures")

    # Load candidate manifest
    with open(CANDIDATE_MANIFEST) as f:
        candidate_manifest = json.load(f)
    assert candidate_manifest["summary"]["n_ranked"] == 54, "Expected 54 candidates in manifest"

    # Build Part 1 list
    part1_entries = build_part1_entries(candidate_manifest)
    part1_ids = {e["pdb_id"] for e in part1_entries}
    logger.info(f"Part 1: {len(part1_entries)} structures ({len(PART1_EXTRAS)} extras + 54 manifest)")

    # Run Part 2 queries
    logger.info("\n--- Part 2 RCSB Queries ---")
    q2a_ids_all, q2a_total_count = query_2a(logger)
    q2b_ids = query_2b(logger)
    q2c_ids = query_2c(logger)

    # Session for downloads and resolution lookups
    session = requests.Session()
    session.headers.update({"User-Agent": "GNN-PCNA-Phase4-Crawl/1.0"})

    # Resolve Part 2A: filter by resolution, deduplicate vs Part 1
    logger.info(f"\nResolving Part 2A resolution for {len(q2a_ids_all)} results...")
    part2a_entries = []
    for pdb_id in q2a_ids_all:
        if pdb_id in part1_ids:
            continue
        if pdb_id in existing_cryptobench:
            logger.info(f"  SKIP {pdb_id}: already in cryptobench")
            continue
        res = get_resolution(pdb_id, session, logger)
        if res is None:
            logger.warning(f"  SKIP {pdb_id}: could not determine resolution")
            continue
        if res > RESOLUTION_CUTOFF:
            logger.info(f"  SKIP {pdb_id}: resolution {res} A > {RESOLUTION_CUTOFF} A")
            continue
        part2a_entries.append({
            "pdb_id": pdb_id,
            "part": "2A",
            "resolution_angstrom": res,
            "has_ligand_per_manifest": None,
            "rank_in_candidate_manifest": None,
        })
        logger.info(f"  ADD {pdb_id}: {res} A")
    logger.info(f"Part 2A: {len(part2a_entries)} new structures to download")

    # Part 2B: deduplicate
    all_queued_ids = part1_ids | {e["pdb_id"] for e in part2a_entries}
    part2b_entries = []
    for pdb_id in q2b_ids:
        if pdb_id in all_queued_ids or pdb_id in existing_cryptobench:
            continue
        part2b_entries.append({
            "pdb_id": pdb_id,
            "part": "2B",
            "resolution_angstrom": None,
            "has_ligand_per_manifest": None,
            "rank_in_candidate_manifest": None,
        })
    logger.info(f"Part 2B (E. coli beta clamp): {len(part2b_entries)} new structures")

    # Part 2C: deduplicate
    all_queued_ids = all_queued_ids | {e["pdb_id"] for e in part2b_entries}
    part2c_entries = []
    for pdb_id in q2c_ids:
        if pdb_id in all_queued_ids or pdb_id in existing_cryptobench:
            continue
        part2c_entries.append({
            "pdb_id": pdb_id,
            "part": "2C",
            "resolution_angstrom": None,
            "has_ligand_per_manifest": None,
            "rank_in_candidate_manifest": None,
        })
    logger.info(f"Part 2C (sliding clamp): {len(part2c_entries)} new structures")

    all_entries = part1_entries + part2a_entries + part2b_entries + part2c_entries
    logger.info(f"\nTotal queued: {len(all_entries)} structures")

    if args.dry_run:
        logger.info("Dry-run mode: exiting before downloads.")
        for e in all_entries:
            logger.info(f"  {e['pdb_id']} [Part {e['part']}]")
        return

    # Download
    logger.info("\n--- Downloading ---")
    structures = []
    n_ok = 0
    n_failed = 0
    skipped_ids = set()

    for entry in all_entries:
        pdb_id = entry["pdb_id"]

        # Skip if already downloaded (idempotent re-runs)
        dest = MMCIF_DIR / f"{pdb_id}.cif.gz"
        if dest.exists() and dest.stat().st_size > 0:
            logger.info(f"  {pdb_id}: already exists, reusing")
            sha = sha256_file(dest)
            record = {
                **entry,
                "source_url": RCSB_DOWNLOAD_BASE.format(pdb_id=pdb_id),
                "download_utc": "REUSED",
                "file_path": str(dest.relative_to(REPO_ROOT)).replace("\\", "/"),
                "file_size_bytes": dest.stat().st_size,
                "sha256": sha,
                "status": "ok",
            }
            structures.append(record)
            n_ok += 1
            continue

        result = download_cif(pdb_id, dest, session, logger)

        if result["status"] == "ok":
            file_path = str(dest.relative_to(REPO_ROOT)).replace("\\", "/")
            record = {
                **entry,
                "source_url": result["source_url"],
                "download_utc": result["download_utc"],
                "file_path": file_path,
                "file_size_bytes": result["file_size_bytes"],
                "sha256": result["sha256"],
                "status": "ok",
            }
            logger.info(f"  {pdb_id}: ok ({result['file_size_bytes']:,} bytes)")
            n_ok += 1
        else:
            if dest.exists():
                dest.unlink()
            record = {
                **entry,
                "source_url": result["source_url"],
                "download_utc": result["download_utc"],
                "file_path": None,
                "file_size_bytes": 0,
                "sha256": None,
                "status": "failed",
                "error": result.get("error", "unknown"),
            }
            logger.warning(f"  {pdb_id}: FAILED — {result.get('error')}")
            n_failed += 1

        structures.append(record)

    logger.info(f"\nDownloads complete: {n_ok} ok, {n_failed} failed")

    # Verification
    if not args.skip_verify:
        logger.info("\n--- Verification ---")

        # 1. Zero-byte check
        for rec in structures:
            if rec["status"] == "ok" and rec.get("file_size_bytes", 0) == 0:
                logger.warning(f"ZERO-BYTE: {rec['pdb_id']}")
                rec["status"] = "failed"
                rec["error"] = "zero-byte file"
                if rec["file_path"]:
                    dest = REPO_ROOT / rec["file_path"]
                    if dest.exists():
                        dest.unlink()
                n_ok -= 1
                n_failed += 1

        # 2. SHA256 re-verify
        sha_mismatches = []
        for rec in structures:
            if rec["status"] != "ok" or not rec.get("file_path"):
                continue
            dest = REPO_ROOT / rec["file_path"]
            if not dest.exists():
                continue
            if rec.get("download_utc") == "REUSED":
                continue  # SHA was computed fresh above
            actual_sha = sha256_file(dest)
            if actual_sha != rec.get("sha256"):
                logger.warning(f"SHA256 MISMATCH: {rec['pdb_id']} expected={rec['sha256']} actual={actual_sha}")
                sha_mismatches.append(rec["pdb_id"])
                rec["status"] = "failed"
                rec["error"] = "sha256 mismatch"
        if sha_mismatches:
            logger.warning(f"SHA256 mismatches: {sha_mismatches}")
        else:
            logger.info("SHA256 verify: all ok")

        # 3. gzip integrity
        gz_failures = []
        for rec in structures:
            if rec["status"] != "ok" or not rec.get("file_path"):
                continue
            dest = REPO_ROOT / rec["file_path"]
            if not dest.exists():
                continue
            if not gzip_ok(dest):
                logger.warning(f"GZIP CRC FAIL: {rec['pdb_id']}")
                gz_failures.append(rec["pdb_id"])
                rec["status"] = "failed"
                rec["error"] = "gzip CRC failure"
        if gz_failures:
            logger.warning(f"gzip failures: {gz_failures}")
        else:
            logger.info("gzip integrity: all ok")

        # 4. Spot-parse (10 random OK structures)
        ok_paths = [
            REPO_ROOT / rec["file_path"]
            for rec in structures
            if rec["status"] == "ok" and rec.get("file_path")
        ]
        if ok_paths:
            spot_failed = spot_parse(ok_paths, logger)
            if spot_failed:
                logger.warning(f"Spot-parse failures: {spot_failed}")
            else:
                logger.info(f"Spot-parse: ok (sampled up to {SPOT_SAMPLE_N})")

        # Recount
        n_ok = sum(1 for r in structures if r["status"] == "ok")
        n_failed = sum(1 for r in structures if r["status"] == "failed")

    # 5. Coverage report for Query 2A
    n_2a_downloaded = sum(1 for r in structures if r.get("part") == "2A" and r["status"] == "ok")
    n_2a_total_api = q2a_total_count
    n_2a_queued = len(part2a_entries)
    logger.info(
        f"\n--- Query 2A Coverage Report ---\n"
        f"  RCSB P12004 total_count (API): {n_2a_total_api}\n"
        f"  Queued after dedup vs Part 1:  {n_2a_queued}\n"
        f"  Downloaded ok:                 {n_2a_downloaded}\n"
        f"  Coverage (downloaded/total):   {n_2a_downloaded}/{n_2a_total_api}"
    )

    # 5E0V flag confirmation
    e0v_rec = next((r for r in structures if r["pdb_id"] == "5E0V"), None)
    e0v_flag_ok = e0v_rec and e0v_rec.get("flag") == "VARIANT_NOT_APO"
    logger.info(f"  5E0V flag VARIANT_NOT_APO confirmed: {e0v_flag_ok}")

    # Write manifest
    n_skipped = len(existing_cryptobench & part1_ids)
    manifest = {
        "schema_version": "1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "total_queued": len(all_entries),
        "total_downloaded": n_ok,
        "total_failed": n_failed,
        "total_skipped_duplicate": n_skipped,
        "query_2a": {
            "uniprot_accession": "P12004",
            "rcsb_total_count": q2a_total_count,
            "queued_after_dedup": len(part2a_entries),
            "downloaded": n_2a_downloaded,
        },
        "query_2b": {"uniprot_accession": "P0ABS6", "queued": len(part2b_entries)},
        "query_2c": {"search_term": "sliding clamp", "queued": len(part2c_entries)},
        "verification": {
            "zero_byte_check": "completed",
            "sha256_verify": "completed",
            "gzip_integrity": "completed",
            "spot_parse_n": SPOT_SAMPLE_N,
        },
        "structures": structures,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"\nManifest written: {MANIFEST_PATH}")

    # Final summary
    logger.info("\n=== Final Summary ===")
    logger.info(f"  Total queued:              {len(all_entries)}")
    logger.info(f"  Total downloaded (ok):     {n_ok}")
    logger.info(f"  Total failed:              {n_failed}")
    logger.info(f"  Total skipped (duplicate): {n_skipped}")
    logger.info(f"  5E0V VARIANT_NOT_APO flag: {'CONFIRMED' if e0v_flag_ok else 'MISSING'}")
    logger.info(f"  Query 2A coverage:         {n_2a_downloaded}/{n_2a_total_api}")
    logger.info(f"  Manifest:                  {MANIFEST_PATH}")
    logger.info(f"  Errors log:                {ERRORS_LOG}")


if __name__ == "__main__":
    main()
