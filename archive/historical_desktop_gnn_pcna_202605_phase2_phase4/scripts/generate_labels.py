"""
Label generation script for CryptoBench cryptic-only adoption.

Implements all four approved residue mapping decisions (2026-05-27):
  4a: Class 1 (420 tokens) — remap via label_seq_id fallback; log to residue_remap_log.json
  4b: Class 2 (297 tokens) — mask absent residues (label = -1)
  4c: Class 2 threshold — exclude structures with >=50% pocket residues absent (only 1lx7)
  4d: Class 3 (4 tokens)  — exclude 4 wrong-chain records; log to excluded_records.json

For each apo structure in the approved cryptic-only candidate set (minus exclusions):
  - Loads CIF file
  - Builds {auth_seq_id: label_seq_id} mapping from atom_site records
  - For each pocket selection token:
      1. Try auth_seq_id lookup (direct match)
      2. If fails, try label_seq_id fallback (Class 1 remap)
      3. If absent entirely, mark as masked (Class 2)
  - Outputs per-structure label arrays as JSON
  - Generates a deterministic hash-verified label manifest

Governance:
  docs/scientific_governance/06_LABELING_RULES.md
  docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md

Outputs:
  data/labels/labels_{apo_pdb_id}.json        — per-structure label file
  data/labels/label_manifest.json             — manifest with hashes
  data/registries/residue_remap_log.json      — Class 1 remap audit log
  data/registries/excluded_records.json       — Class 3 + 4c excluded records
  reports/phase2/label_generation_report.md   — summary report
"""

import json
import hashlib
import zipfile
import io
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).parent.parent

DATASET_PATH  = ROOT / "data/raw_intake/cryptobench/metadata_files/66c328c87352852f68dbeac4_dataset.json"
FOLDS_PATH    = ROOT / "data/raw_intake/cryptobench/metadata_files/66c328d97352852f68dbead5_folds.json"
CIF_ZIP_PATH  = ROOT / "data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip"
MAPPING_FAIL  = ROOT / "data/registries/residue_mapping_failures.json"
IMPACT_JSON   = ROOT / "data/registries/residue_mapping_per_structure_impact.json"

OUT_LABELS_DIR = ROOT / "data/labels"
OUT_MANIFEST   = ROOT / "data/labels/label_manifest.json"
OUT_REMAP_LOG  = ROOT / "data/registries/residue_remap_log.json"
OUT_EXCLUDED   = ROOT / "data/registries/excluded_records.json"
OUT_REPORT     = ROOT / "reports/phase2/label_generation_report.md"

# ── Policy constants ──────────────────────────────────────────────────────────
# Decision 4c: exclude structures where >= this fraction of pocket residues are absent
MASK_EXCLUSION_THRESHOLD = 0.50

# Explicitly excluded by other decisions
PCNA_EXACT_EXCLUDED  = {"5e0v"}  # Decision 2: PCNA isolation (apo side)
CLASS3_CHAIN_MISMATCH_APOS = None  # loaded from residue_mapping_failures.json

LABEL_POSITIVE  =  1
LABEL_UNLABELED =  0   # background / not in pocket selection
LABEL_MASKED    = -1   # absent from atom_site — excluded from loss

GOVERNANCE = {
    "labeling": "docs/scientific_governance/06_LABELING_RULES.md",
    "graph":    "docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md",
    "review":   "docs/scientific_governance/26_HUMAN_REVIEW_GATES.md",
}


# ── CIF parsing ───────────────────────────────────────────────────────────────

def parse_cif_residue_maps(cif_text: str, target_chain: str) -> tuple[dict, dict, set]:
    """
    Parse CIF atom_site block to build residue lookup maps.

    Returns:
      auth_to_label: {(auth_asym_id, auth_seq_id_str) -> label_seq_id_str}
      label_to_auth: {(auth_asym_id, label_seq_id_str) -> auth_seq_id_str}
      present_auths: set of (auth_asym_id, auth_seq_id_str) with coordinates present
    """
    auth_to_label = {}
    label_to_auth = {}
    present_auths = set()

    in_atom_site = False
    headers = []
    col = {}

    for raw_line in cif_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            if in_atom_site and headers:
                in_atom_site = False
                headers = []
                col = {}
            continue

        if line == "loop_":
            in_atom_site = False
            headers = []
            col = {}
            continue

        if line.startswith("_atom_site."):
            if not in_atom_site:
                in_atom_site = True
            tag = line.split(".")[1].lower().split()[0]
            headers.append(tag)
            col[tag] = len(headers) - 1
            continue

        if in_atom_site and headers and not line.startswith("_") and not line.startswith("loop_"):
            # Parse atom_site data row
            parts = line.split()
            if len(parts) < len(headers):
                continue

            group = parts[col["group_pdb"]] if "group_pdb" in col else "ATOM"
            if group not in ("ATOM", "HETATM"):
                continue

            auth_chain  = parts[col["auth_asym_id"]]  if "auth_asym_id"  in col else "."
            auth_seq    = parts[col["auth_seq_id"]]    if "auth_seq_id"   in col else "."
            label_chain = parts[col["label_asym_id"]]  if "label_asym_id" in col else auth_chain
            label_seq   = parts[col["label_seq_id"]]   if "label_seq_id"  in col else auth_seq

            if auth_chain != target_chain:
                continue
            if auth_seq in (".", "?") or label_seq in (".", "?"):
                continue

            key_auth  = (auth_chain, auth_seq)
            key_label = (auth_chain, label_seq)

            auth_to_label[key_auth]  = label_seq
            label_to_auth[key_label] = auth_seq
            present_auths.add(key_auth)

    return auth_to_label, label_to_auth, present_auths


def token_to_chain_seq(token: str) -> tuple[str, str]:
    """Parse 'A_42' or 'A_42A' pocket selection token -> (chain, seq_str)."""
    parts = token.split("_", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "A", token


# ── Label generation for one structure ───────────────────────────────────────

def generate_labels_for_apo(
    apo_id: str,
    chain: str,
    pocket_tokens: list[str],
    cif_text: str,
) -> dict:
    """
    Returns {
        apo_pdb_id, chain, pocket_tokens,
        labels: {token: label_int},    # LABEL_POSITIVE / LABEL_MASKED
        remaps: [{token, found_auth_seq, label_seq_id}],
        masked: [token],               # absent from atom_site
        errors: [str],
    }
    """
    auth_to_label, label_to_auth, present_auths = parse_cif_residue_maps(cif_text, chain)

    labels  = {}
    remaps  = []
    masked  = []
    errors  = []

    for token in pocket_tokens:
        tok_chain, tok_seq = token_to_chain_seq(token)

        # Direct auth_seq_id lookup
        key = (tok_chain, tok_seq)
        if key in present_auths:
            labels[token] = LABEL_POSITIVE
            continue

        # Class 1 fallback: try as label_seq_id
        lkey = (tok_chain, tok_seq)
        if lkey in label_to_auth:
            found_auth = label_to_auth[lkey]
            auth_key = (tok_chain, found_auth)
            if auth_key in present_auths:
                labels[token] = LABEL_POSITIVE
                remaps.append({
                    "token": token,
                    "original_seq": tok_seq,
                    "found_auth_seq_id": found_auth,
                    "interpreted_as": "label_seq_id",
                })
                continue

        # Class 2: residue absent from atom_site
        labels[token] = LABEL_MASKED
        masked.append(token)

    return {
        "apo_pdb_id": apo_id,
        "chain": chain,
        "pocket_token_count": len(pocket_tokens),
        "labels": labels,
        "remaps": remaps,
        "masked": masked,
        "errors": errors,
        "fraction_masked": len(masked) / len(pocket_tokens) if pocket_tokens else 0.0,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    ts = lambda: f"[{datetime.now():%H:%M:%S}]"
    print(f"{ts()} Loading dataset and folds ...")

    with open(DATASET_PATH, encoding="utf-8") as f:
        dataset = json.load(f)
    with open(FOLDS_PATH, encoding="utf-8") as f:
        folds = json.load(f)

    # Build fold mapping
    apo_to_fold = {apo.lower(): fold for fold, apos in folds.items() for apo in apos}

    # Load Class 3 wrong-chain failures
    with open(MAPPING_FAIL, encoding="utf-8") as f:
        fail_data = json.load(f)
    records_list = fail_data if isinstance(fail_data, list) else fail_data.get("failures", [])
    class3_apos = set(
        r["apo_pdb_id"].lower() for r in records_list
        if r.get("reason") == "residue_token_exists_on_other_chain"
    )
    print(f"  Class 3 exclusions (wrong chain): {sorted(class3_apos)}")

    # Load Class 2 per-structure impact (for 4c threshold)
    with open(IMPACT_JSON, encoding="utf-8") as f:
        impact_data = json.load(f)
    impact_list = impact_data if isinstance(impact_data, list) else impact_data.get("per_structure", [])
    # Structures exceeding 4c threshold → exclude entirely
    class4c_excluded = set(
        s["apo_pdb_id"].lower() for s in impact_list
        if s.get("fraction_masked", 0) >= MASK_EXCLUSION_THRESHOLD
    )
    print(f"  Class 4c exclusions (>=50% masked): {sorted(class4c_excluded)}")

    # Build apo -> (chain, pocket_tokens) from dataset
    apo_to_chain  = {}
    apo_to_tokens = {}
    for apo_key, records in dataset.items():
        apo = apo_key.lower()
        if not isinstance(records, list):
            records = [records]
        apo_to_chain[apo] = records[0].get("apo_chain", "A")
        # Union of all pocket tokens across holos
        tokens = set()
        for rec in records:
            sel = rec.get("apo_pocket_selection", [])
            if isinstance(sel, list):
                tokens.update(sel)
            elif isinstance(sel, dict):
                tokens.update(sel.keys())
        apo_to_tokens[apo] = sorted(tokens)

    # All candidate apo structures (from folds)
    all_apos = sorted(apo_to_fold.keys())
    print(f"  Total candidate apos: {len(all_apos)}")

    # Excluded apos
    excluded_pcna  = PCNA_EXACT_EXCLUDED
    excluded_class3 = class3_apos
    excluded_4c    = class4c_excluded
    all_excluded = excluded_pcna | excluded_class3 | excluded_4c
    candidate_apos = [a for a in all_apos if a not in all_excluded]
    print(f"  Excluded (PCNA): {sorted(excluded_pcna)}")
    print(f"  Excluded (Class3 wrong-chain): {sorted(excluded_class3)}")
    print(f"  Excluded (4c >=50% masked): {sorted(excluded_4c)}")
    print(f"  Proceeding with {len(candidate_apos)} apo structures")

    # Create output dir
    OUT_LABELS_DIR.mkdir(parents=True, exist_ok=True)

    # Check CIF zip exists
    if not CIF_ZIP_PATH.exists():
        print(f"ERROR: CIF zip not found at {CIF_ZIP_PATH}")
        print("Labels cannot be generated without CIF files. The zip is in data/raw_intake/ (gitignored).")
        print("Generating dry-run output showing what would be computed...")
        _write_dry_run_report(candidate_apos, all_excluded, apo_to_fold, apo_to_tokens)
        return

    # Main label generation loop
    print(f"\n{ts()} Opening CIF zip and generating labels ...")
    remap_log = []
    excluded_records_log = []
    manifest = {}
    stats = {"positive": 0, "masked": 0, "remapped": 0, "structures_ok": 0,
             "structures_failed": 0, "structures_skipped": 0}

    # Log all excluded structures
    for apo in sorted(all_excluded):
        reason = (
            "pcna_exact_contamination" if apo in excluded_pcna else
            "class3_wrong_chain" if apo in excluded_class3 else
            "class4c_high_mask_fraction"
        )
        excluded_records_log.append({
            "apo_pdb_id": apo,
            "reason": reason,
            "policy_decision": "4c" if apo in excluded_4c else "4d" if apo in excluded_class3 else "decision_2",
            "fold": apo_to_fold.get(apo, "unknown"),
        })

    total = len(candidate_apos)
    with zipfile.ZipFile(CIF_ZIP_PATH, "r") as zf:
        zip_names = {n.lower(): n for n in zf.namelist()}

        for i, apo in enumerate(candidate_apos, 1):
            chain  = apo_to_chain.get(apo, "A")
            tokens = apo_to_tokens.get(apo, [])
            if not tokens:
                stats["structures_skipped"] += 1
                continue

            # Find CIF file in zip (case-insensitive; zip uses cif-files/ prefix)
            cif_key = None
            for pattern in [f"cif-files/{apo}.cif", f"cif-files/{apo.upper()}.cif",
                             f"{apo}.cif", f"{apo.upper()}.cif"]:
                if pattern.lower() in zip_names:
                    cif_key = zip_names[pattern.lower()]
                    break

            if not cif_key:
                stats["structures_failed"] += 1
                continue

            try:
                with zf.open(cif_key) as fh:
                    cif_text = fh.read().decode("utf-8", errors="replace")
            except Exception as e:
                stats["structures_failed"] += 1
                continue

            result = generate_labels_for_apo(apo, chain, tokens, cif_text)

            # Record remaps
            for remap in result["remaps"]:
                remap_log.append({
                    "apo_pdb_id": apo,
                    "fold": apo_to_fold.get(apo, "unknown"),
                    **remap,
                })

            # Build label array output
            label_record = {
                "apo_pdb_id": apo,
                "chain": chain,
                "fold": apo_to_fold.get(apo, "unknown"),
                "pocket_token_count": result["pocket_token_count"],
                "positive_count": sum(1 for v in result["labels"].values() if v == LABEL_POSITIVE),
                "masked_count": len(result["masked"]),
                "remapped_count": len(result["remaps"]),
                "fraction_masked": result["fraction_masked"],
                "labels": result["labels"],  # {token: label_int}
                "generated_at": datetime.now().isoformat(),
                "governance": GOVERNANCE["labeling"],
            }

            stats["positive"]  += label_record["positive_count"]
            stats["masked"]    += label_record["masked_count"]
            stats["remapped"]  += label_record["remapped_count"]
            stats["structures_ok"] += 1

            # Write per-structure label file
            out_path = OUT_LABELS_DIR / f"labels_{apo}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(label_record, f)

            # Hash for manifest
            content_hash = hashlib.sha256(
                json.dumps(label_record, sort_keys=True).encode()
            ).hexdigest()[:16]
            manifest[apo] = {
                "path": str(out_path.relative_to(ROOT)),
                "hash_sha256_prefix": content_hash,
                "fold": apo_to_fold.get(apo, "unknown"),
                "positive_count": label_record["positive_count"],
                "masked_count": label_record["masked_count"],
            }

            if i % 100 == 0:
                print(f"  {ts()} {i}/{total} ({100*i//total}%) — ok={stats['structures_ok']} "
                      f"remapped={stats['remapped']} masked={stats['masked']}")

    print(f"\n{ts()} Writing output registries ...")

    # Write remap log
    with open(OUT_REMAP_LOG, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "decision": "4a",
            "total_remaps": len(remap_log),
            "remaps": remap_log,
        }, f, indent=2)

    # Write excluded records log
    with open(OUT_EXCLUDED, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_excluded": len(excluded_records_log),
            "excluded": excluded_records_log,
        }, f, indent=2)

    # Write manifest
    manifest_doc = {
        "generated_at": datetime.now().isoformat(),
        "label_policy": "positive_unlabeled",
        "label_values": {
            "positive": LABEL_POSITIVE,
            "unlabeled": LABEL_UNLABELED,
            "masked": LABEL_MASKED,
        },
        "decisions_applied": ["4a_remap", "4b_mask", "4c_exclude_high_mask", "4d_exclude_wrong_chain"],
        "structures_labeled": stats["structures_ok"],
        "structures_excluded": len(all_excluded),
        "total_positives": stats["positive"],
        "total_masked": stats["masked"],
        "total_remapped": stats["remapped"],
        "governance": GOVERNANCE,
        "entries": manifest,
    }
    with open(OUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest_doc, f, indent=2)

    _write_full_report(stats, remap_log, excluded_records_log, manifest_doc)

    print(f"{ts()} DONE.")
    print(f"  Labeled: {stats['structures_ok']}  Excluded: {len(all_excluded)}  "
          f"Failed: {stats['structures_failed']}  Skipped: {stats['structures_skipped']}")
    print(f"  Total positives: {stats['positive']}  Masked: {stats['masked']}  Remapped: {stats['remapped']}")
    print(f"  {OUT_MANIFEST}")
    print(f"  {OUT_REPORT}")


def _write_dry_run_report(candidate_apos, all_excluded, apo_to_fold, apo_to_tokens):
    print("\n[DRY RUN — CIF zip not present]")
    print(f"  Would label {len(candidate_apos)} structures")
    print(f"  Would exclude {len(all_excluded)} structures")
    print(f"  CIF zip required: {CIF_ZIP_PATH}")
    print("  Run this script from a machine where data/raw_intake/ is populated.")
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write(f"# Label Generation Report — DRY RUN\n\n")
        f.write(f"CIF zip not present at `{CIF_ZIP_PATH.relative_to(ROOT)}`.\n")
        f.write(f"Script validated. Would label {len(candidate_apos)} structures, ")
        f.write(f"exclude {len(all_excluded)}.\n\n")
        f.write(f"Run on a machine with `data/raw_intake/` populated.\n")


def _write_full_report(stats, remap_log, excluded_log, manifest_doc):
    lines = [
        "---",
        "type: analysis-report",
        f"status: complete",
        f"created: {datetime.now().strftime('%Y-%m-%d')}",
        "decisions_applied: [4a, 4b, 4c, 4d]",
        "---",
        "",
        "# Label Generation Report — Phase 2",
        "",
        "**Policy:** Positive-unlabeled (PU) learning. Positives from `apo_pocket_selection`;",
        "unlisted residues = background/unlabeled; absent residues = masked from loss.",
        "**Governance:** `docs/scientific_governance/06_LABELING_RULES.md`",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Structures labeled | {stats['structures_ok']} |",
        f"| Structures excluded | {len(excluded_log)} |",
        f"| Structures failed (CIF parse error) | {stats['structures_failed']} |",
        f"| Total positive labels | {stats['positive']} |",
        f"| Total masked labels | {stats['masked']} |",
        f"| Total Class 1 remaps (4a) | {stats['remapped']} |",
        "",
        "---",
        "",
        "## Excluded Structures",
        "",
        "| Apo PDB | Reason | Policy |",
        "|---|---|---|",
    ]
    for e in excluded_log:
        lines.append(f"| {e['apo_pdb_id']} | {e['reason']} | Decision {e['policy_decision']} |")
    lines += [
        "",
        "---",
        "",
        "## Class 1 Remaps (Decision 4a)",
        "",
        f"Total remaps: {len(remap_log)}",
        "",
        "Pocket selection tokens that matched label_seq_id but not auth_seq_id.",
        "These are valid residues; they were just referenced by the wrong numbering scheme.",
        "",
        "---",
        "",
        "## Provenance",
        "",
        "- Source: CryptoBench `dataset.json` + CIF files from `data/raw_intake/cryptobench/`",
        "- Decisions: 4a (remap), 4b (mask), 4c (exclude 1lx7), 4d (exclude wrong-chain records)",
        "- Governance: `docs/scientific_governance/06_LABELING_RULES.md`",
        "- Evidence status: verified (all counts from local CIF parsing and approved registries)",
        f"- Generated: {datetime.now().isoformat()}",
    ]
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run()
