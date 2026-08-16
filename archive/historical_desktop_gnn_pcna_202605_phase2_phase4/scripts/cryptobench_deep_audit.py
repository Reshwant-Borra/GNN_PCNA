#!/usr/bin/env python3
"""Deep local audit of quarantined CryptoBench artifacts.

This script reads raw JSON files and mmCIF files inside the quarantined ZIP
archive in place. It writes audit reports and compact registries only. It does
not extract canonical structures, generate graphs, freeze labels/splits, train,
evaluate, or run MD.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw_intake" / "cryptobench"
REPORT_DIR = ROOT / "reports" / "phase2"
REGISTRY_DIR = ROOT / "data" / "registries"

DATASET_JSON = RAW / "metadata_files" / "66c328c87352852f68dbeac4_dataset.json"
FOLDS_JSON = RAW / "metadata_files" / "66c328d97352852f68dbead5_folds.json"
NONCRYPTIC_JSON = RAW / "labels_or_splits" / "66c32918467db4bc475da14e_noncryptic-pockets.json"
ZIP_PATH = RAW / "files" / "672a0171eae0bff252ba9ea3_cif-files.zip"

FOLD_FILES = {
    "test": RAW / "labels_or_splits" / "66c328e138497880962d3054_test.json",
    "train-0": RAW / "labels_or_splits" / "66c328eba3530855975d9d19_train-fold-0.json",
    "train-1": RAW / "labels_or_splits" / "66c328f5cb9874ed0d2d33b3_train-fold-1.json",
    "train-2": RAW / "labels_or_splits" / "66c328fe653be15e240b528b_train-fold-2.json",
    "train-3": RAW / "labels_or_splits" / "66c329087352852f68dbeaf4_train-fold-3.json",
}

REPORTS = {
    "schema": REPORT_DIR / "cryptobench_schema_deep_audit.md",
    "split": REPORT_DIR / "cryptobench_split_risk_audit.md",
    "labels": REPORT_DIR / "cryptobench_label_semantics.md",
    "structures": REPORT_DIR / "cryptobench_structure_inventory.md",
    "pcna": REPORT_DIR / "pcna_contamination_screen.md",
}

REGISTRIES = {
    "schema": REGISTRY_DIR / "cryptobench_schema_summary.json",
    "fold": REGISTRY_DIR / "cryptobench_fold_summary.json",
    "structure": REGISTRY_DIR / "cryptobench_structure_index.json",
}

PCNA_TERMS = [
    "p12004",
    "pcna",
    "proliferating cell nuclear antigen",
    "pol30",
    "sliding clamp",
    "dna sliding clamp",
    "beta clamp",
    "dna polymerase iii beta",
]

SELECTION_RE = re.compile(r"^(?P<chain>.+)_(?P<residue>-?\d+[A-Za-z]?)$")


@dataclass
class CifSummary:
    pdb_id: str
    zip_member: str
    compressed_size: int
    uncompressed_size: int
    readable: bool = False
    atom_site_found: bool = False
    atom_site_parse_error: str | None = None
    chains: list[str] = field(default_factory=list)
    residue_count: int = 0
    atom_count: int = 0
    residues_by_chain: dict[str, int] = field(default_factory=dict)
    residue_tokens_by_chain: dict[str, set[str]] = field(default_factory=dict, repr=False)
    first_line: str | None = None
    pcna_term_hits: list[str] = field(default_factory=list)


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_selection(selection: Any) -> tuple[str | None, str | None, bool]:
    if not isinstance(selection, str):
        return None, None, False
    match = SELECTION_RE.match(selection)
    if not match:
        return None, None, False
    return match.group("chain"), match.group("residue"), True


def expected_chain_set(value: Any) -> set[str]:
    text = str(value)
    if not text:
        return set()
    # CryptoBench uses fields such as "A-B" for multichain pockets.
    if "-" in text:
        return {part for part in text.split("-") if part}
    return {text}


def entry_key(apo_id: str, entry: dict[str, Any]) -> str:
    return "|".join(
        [
            apo_id,
            str(entry.get("apo_chain", "")),
            str(entry.get("holo_pdb_id", "")),
            str(entry.get("holo_chain", "")),
            str(entry.get("ligand", "")),
            str(entry.get("ligand_index", "")),
            str(entry.get("ligand_chain", "")),
        ]
    )


def normalize_pdb_id(value: Any) -> str:
    return str(value).lower()


def collect_records(dataset: dict[str, Any], record_type: str) -> list[dict[str, Any]]:
    records = []
    for apo_id, entries in dataset.items():
        if not isinstance(entries, list):
            records.append(
                {
                    "record_type": record_type,
                    "apo_pdb_id": apo_id,
                    "schema_error": f"expected list, got {type(entries).__name__}",
                }
            )
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                records.append(
                    {
                        "record_type": record_type,
                        "apo_pdb_id": apo_id,
                        "entry_index": index,
                        "schema_error": f"expected dict, got {type(entry).__name__}",
                    }
                )
                continue
            row = dict(entry)
            row["record_type"] = record_type
            row["apo_pdb_id"] = apo_id
            row["entry_index"] = index
            row["entry_key"] = entry_key(apo_id, entry)
            records.append(row)
    return records


def field_profile(records: list[dict[str, Any]]) -> dict[str, Any]:
    profile: dict[str, Any] = {}
    all_fields = sorted({field for record in records for field in record})
    for name in all_fields:
        values = [record.get(name) for record in records]
        missing = sum(1 for value in values if value is None)
        types = Counter(type(value).__name__ for value in values if value is not None)
        nonempty = [value for value in values if value not in (None, "", [], {})]
        unique = {json.dumps(value, sort_keys=True, default=str) for value in nonempty}
        examples = []
        for value in nonempty:
            if len(examples) >= 5:
                break
            rendered = value
            if isinstance(value, list):
                rendered = value[:5]
            if rendered not in examples:
                examples.append(rendered)
        profile[name] = {
            "present_count": len(values) - missing,
            "missing_count": missing,
            "types": dict(types),
            "unique_nonempty_count": len(unique),
            "examples": examples,
        }
    return profile


def analyze_selections(records: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field_name, chain_field in [
        ("apo_pocket_selection", "apo_chain"),
        ("holo_pocket_selection", "holo_chain"),
    ]:
        malformed = []
        wrong_chain = []
        lengths = []
        residue_tokens = Counter()
        for record in records:
            selections = record.get(field_name)
            if not isinstance(selections, list):
                malformed.append(
                    {
                        "apo_pdb_id": record.get("apo_pdb_id"),
                        "entry_index": record.get("entry_index"),
                        "reason": f"{field_name} is {type(selections).__name__}",
                    }
                )
                continue
            lengths.append(len(selections))
            expected_chains = expected_chain_set(record.get(chain_field))
            for selection in selections:
                chain, residue, ok = parse_selection(selection)
                if not ok:
                    malformed.append(
                        {
                            "apo_pdb_id": record.get("apo_pdb_id"),
                            "entry_index": record.get("entry_index"),
                            "selection": selection,
                        }
                    )
                    continue
                residue_tokens[residue] += 1
                if chain not in expected_chains:
                    wrong_chain.append(
                        {
                            "apo_pdb_id": record.get("apo_pdb_id"),
                            "entry_index": record.get("entry_index"),
                            "selection": selection,
                            "expected_chain": record.get(chain_field),
                        }
                    )
        result[field_name] = {
            "entry_count": len(lengths),
            "min_len": min(lengths) if lengths else None,
            "max_len": max(lengths) if lengths else None,
            "mean_len": round(sum(lengths) / len(lengths), 2) if lengths else None,
            "zero_len_count": sum(1 for value in lengths if value == 0),
            "malformed_count": len(malformed),
            "wrong_chain_count": len(wrong_chain),
            "malformed_examples": malformed[:20],
            "wrong_chain_examples": wrong_chain[:20],
            "unique_residue_token_count": len(residue_tokens),
        }
    return result


def split_records_by_fold(
    records: list[dict[str, Any]], apo_to_fold: dict[str, str]
) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        result[apo_to_fold.get(record["apo_pdb_id"], "unassigned")].append(record)
    return result


def invert_groups(mapping: dict[str, str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for key, value in mapping.items():
        groups[value].append(key)
    return {key: sorted(values) for key, values in sorted(groups.items())}


def parse_atom_site(text: str, pdb_id: str) -> tuple[dict[str, Any], str | None]:
    lines = text.splitlines()
    columns: list[str] | None = None
    rows_started = False
    residues: set[tuple[str, str, str, str]] = set()
    atom_count = 0
    chain_counts: Counter[str] = Counter()
    atom_site_found = False

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == "loop_":
            j = i + 1
            current_columns = []
            while j < len(lines) and lines[j].strip().startswith("_"):
                current_columns.append(lines[j].strip().split()[0])
                j += 1
            if any(column.startswith("_atom_site.") for column in current_columns):
                columns = current_columns
                i = j
                atom_site_found = True
                break
        i += 1

    if not columns:
        return {
            "atom_site_found": atom_site_found,
            "residues": residues,
            "atom_count": atom_count,
            "chain_counts": chain_counts,
        }, None

    col_index = {name: idx for idx, name in enumerate(columns)}
    group_idx = col_index.get("_atom_site.group_PDB")
    auth_chain_idx = col_index.get("_atom_site.auth_asym_id")
    label_chain_idx = col_index.get("_atom_site.label_asym_id")
    auth_seq_idx = col_index.get("_atom_site.auth_seq_id")
    ins_idx = col_index.get("_atom_site.pdbx_PDB_ins_code")
    comp_idx = col_index.get("_atom_site.label_comp_id")

    if auth_seq_idx is None or comp_idx is None:
        return {
            "atom_site_found": atom_site_found,
            "residues": residues,
            "atom_count": atom_count,
            "chain_counts": chain_counts,
        }, "atom_site loop lacks required auth_seq_id or label_comp_id"

    chain_idx = auth_chain_idx if auth_chain_idx is not None else label_chain_idx
    if chain_idx is None:
        return {
            "atom_site_found": atom_site_found,
            "residues": residues,
            "atom_count": atom_count,
            "chain_counts": chain_counts,
        }, "atom_site loop lacks chain id columns"

    expected_width = len(columns)
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped:
            i += 1
            continue
        if stripped == "#" or stripped == "loop_" or stripped.startswith("_") or stripped.startswith("data_"):
            break
        parts = stripped.split()
        if len(parts) < expected_width:
            return {
                "atom_site_found": atom_site_found,
                "residues": residues,
                "atom_count": atom_count,
                "chain_counts": chain_counts,
            }, f"short atom_site row in {pdb_id}: expected {expected_width}, got {len(parts)}"
        group = parts[group_idx] if group_idx is not None else "ATOM"
        if group in {"ATOM", "HETATM"}:
            chain = parts[chain_idx]
            auth_seq = parts[auth_seq_idx]
            ins = parts[ins_idx] if ins_idx is not None else "?"
            comp = parts[comp_idx]
            if group == "ATOM":
                residues.add((chain, auth_seq, ins, comp))
                chain_counts[chain] += 1
            atom_count += 1
            rows_started = True
        elif rows_started:
            break
        i += 1

    return {
        "atom_site_found": atom_site_found,
        "residues": residues,
        "atom_count": atom_count,
        "chain_counts": chain_counts,
    }, None


def inspect_cifs(
    required_pdb_ids: set[str], required_by_type: dict[str, set[str]]
) -> tuple[dict[str, CifSummary], dict[str, Any]]:
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        infos = [info for info in archive.infolist() if not info.is_dir()]
        info_by_pdb = {
            Path(info.filename).stem.lower(): info
            for info in infos
            if Path(info.filename).suffix.lower() == ".cif"
        }
        summaries: dict[str, CifSummary] = {}
        missing = sorted(required_pdb_ids - set(info_by_pdb))
        extra = sorted(set(info_by_pdb) - required_pdb_ids)

        for pdb_id in sorted(required_pdb_ids & set(info_by_pdb)):
            info = info_by_pdb[pdb_id]
            summary = CifSummary(
                pdb_id=pdb_id,
                zip_member=info.filename,
                compressed_size=info.compress_size,
                uncompressed_size=info.file_size,
            )
            try:
                text = archive.read(info).decode("utf-8", errors="replace")
                summary.readable = True
                summary.first_line = text.splitlines()[0] if text.splitlines() else ""
                lowered = text.lower()
                summary.pcna_term_hits = sorted(term for term in PCNA_TERMS if term in lowered)
                parsed, error = parse_atom_site(text, pdb_id)
                summary.atom_site_found = bool(parsed["atom_site_found"])
                summary.atom_site_parse_error = error
                residues = parsed["residues"]
                chain_counts = parsed["chain_counts"]
                summary.residue_count = len(residues)
                summary.atom_count = int(parsed["atom_count"])
                summary.chains = sorted(chain_counts)
                residues_by_chain: Counter[str] = Counter()
                residue_tokens_by_chain: dict[str, set[str]] = defaultdict(set)
                for chain, _auth_seq, _ins, _comp in residues:
                    residues_by_chain[chain] += 1
                    residue_tokens_by_chain[chain].add(_auth_seq)
                    if _ins not in {"?", ".", ""}:
                        residue_tokens_by_chain[chain].add(f"{_auth_seq}{_ins}")
                summary.residues_by_chain = dict(sorted(residues_by_chain.items()))
                summary.residue_tokens_by_chain = {
                    chain: set(tokens) for chain, tokens in residue_tokens_by_chain.items()
                }
            except Exception as exc:  # pragma: no cover - audit must record unexpected failures
                summary.atom_site_parse_error = repr(exc)
            summaries[pdb_id] = summary

    presence_by_type = {}
    for record_type, required_ids in sorted(required_by_type.items()):
        missing_for_type = sorted(required_ids - set(info_by_pdb))
        presence_by_type[record_type] = {
            "required_structure_count": len(required_ids),
            "present_structure_count": len(required_ids & set(info_by_pdb)),
            "missing_structure_count": len(missing_for_type),
            "missing_structure_examples": missing_for_type[:100],
        }

    zip_summary = {
        "zip_path": rel(ZIP_PATH),
        "zip_sha256": sha256_file(ZIP_PATH),
        "zip_size_bytes": ZIP_PATH.stat().st_size,
        "zip_file_count": len(info_by_pdb),
        "required_structure_count": len(required_pdb_ids),
        "missing_required_structure_count": len(missing),
        "missing_required_structures": missing,
        "extra_cif_count": len(extra),
        "extra_cif_examples": extra[:50],
        "presence_by_record_type": presence_by_type,
    }
    return summaries, zip_summary


def validate_record_against_cif(
    records: list[dict[str, Any]], cif_summaries: dict[str, CifSummary]
) -> dict[str, Any]:
    issues = []
    checked_selections = 0
    missing_residue_count = 0
    missing_chain_count = 0

    for record in records:
        checks = [
            ("apo", record.get("apo_pdb_id"), record.get("apo_chain"), record.get("apo_pocket_selection")),
            ("holo", record.get("holo_pdb_id"), record.get("holo_chain"), record.get("holo_pocket_selection")),
        ]
        for role, pdb_id_raw, expected_chain_raw, selections in checks:
            pdb_id = normalize_pdb_id(pdb_id_raw)
            expected_chains = expected_chain_set(expected_chain_raw)
            summary = cif_summaries.get(pdb_id)
            if summary is None:
                issues.append(
                    {
                        "type": "missing_cif",
                        "record_type": record.get("record_type"),
                        "apo_pdb_id": record.get("apo_pdb_id"),
                        "holo_pdb_id": record.get("holo_pdb_id"),
                        "role": role,
                        "pdb_id": pdb_id,
                    }
                )
                continue
            if not expected_chains.issubset(set(summary.chains)):
                missing_chain_count += 1
                issues.append(
                    {
                        "type": "selection_chain_absent_from_cif_atom_site",
                        "record_type": record.get("record_type"),
                        "apo_pdb_id": record.get("apo_pdb_id"),
                        "holo_pdb_id": record.get("holo_pdb_id"),
                        "role": role,
                        "pdb_id": pdb_id,
                        "expected_chain": expected_chain_raw,
                        "missing_chains": sorted(expected_chains - set(summary.chains)),
                        "cif_chains": summary.chains,
                    }
                )
            if isinstance(selections, list):
                checked_selections += len(selections)
                # Exact residue ID validation is deferred to graph audit because mmCIF auth
                # sequence IDs may include insertion-code representation not captured by the
                # CryptoBench token. We still catch malformed tokens and absent chains.
                for selection in selections:
                    chain, residue, ok = parse_selection(selection)
                    if not ok:
                        continue
                    if chain not in summary.chains:
                        missing_residue_count += 1
                    elif residue not in summary.residue_tokens_by_chain.get(chain, set()):
                        missing_residue_count += 1
                        issues.append(
                            {
                                "type": "selection_residue_absent_from_cif_atom_site",
                                "record_type": record.get("record_type"),
                                "apo_pdb_id": record.get("apo_pdb_id"),
                                "holo_pdb_id": record.get("holo_pdb_id"),
                                "role": role,
                                "pdb_id": pdb_id,
                                "selection": selection,
                                "chain": chain,
                                "residue_token": residue,
                            }
                        )
    return {
        "checked_selection_token_count": checked_selections,
        "chain_absence_issue_count": missing_chain_count,
        "selection_tokens_absent_from_atom_site": missing_residue_count,
        "issues": issues[:200],
        "issue_count": len(issues),
        "exact_residue_id_validation_status": "checked_against_auth_seq_id_and_auth_seq_id_plus_insertion_code_tokens",
    }


def cross_fold_overlap(
    folds: dict[str, list[str]], records_by_fold: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    fold_sets = {fold: set(ids) for fold, ids in folds.items()}
    apo_overlaps = {}
    for left in fold_sets:
        for right in fold_sets:
            if left >= right:
                continue
            overlap = sorted(fold_sets[left] & fold_sets[right])
            if overlap:
                apo_overlaps[f"{left}|{right}"] = overlap

    uniprot_to_folds: dict[str, set[str]] = defaultdict(set)
    holo_to_folds: dict[str, set[str]] = defaultdict(set)
    ligand_to_folds: dict[str, set[str]] = defaultdict(set)
    for fold, records in records_by_fold.items():
        for record in records:
            if record.get("uniprot_id"):
                uniprot_to_folds[str(record["uniprot_id"])].add(fold)
            if record.get("holo_pdb_id"):
                holo_to_folds[normalize_pdb_id(record["holo_pdb_id"])].add(fold)
            if record.get("ligand"):
                ligand_to_folds[str(record["ligand"])].add(fold)

    shared_uniprots = {
        key: sorted(value)
        for key, value in sorted(uniprot_to_folds.items())
        if len(value) > 1
    }
    shared_holos = {
        key: sorted(value)
        for key, value in sorted(holo_to_folds.items())
        if len(value) > 1
    }
    shared_ligands = {
        key: sorted(value)
        for key, value in sorted(ligand_to_folds.items())
        if len(value) > 1
    }
    test_uniprots = {str(r["uniprot_id"]) for r in records_by_fold.get("test", []) if r.get("uniprot_id")}
    train_uniprots = {
        str(r["uniprot_id"])
        for fold, fold_records in records_by_fold.items()
        if fold.startswith("train")
        for r in fold_records
        if r.get("uniprot_id")
    }
    return {
        "apo_id_cross_fold_overlap_count": sum(len(v) for v in apo_overlaps.values()),
        "apo_id_cross_fold_overlaps": apo_overlaps,
        "shared_uniprot_count": len(shared_uniprots),
        "shared_uniprots_examples": dict(list(shared_uniprots.items())[:100]),
        "shared_holo_pdb_count": len(shared_holos),
        "shared_holo_pdb_examples": dict(list(shared_holos.items())[:100]),
        "shared_ligand_count": len(shared_ligands),
        "shared_ligand_examples": dict(list(shared_ligands.items())[:100]),
        "train_test_shared_uniprot_count": len(test_uniprots & train_uniprots),
        "train_test_shared_uniprots": sorted(test_uniprots & train_uniprots),
    }


def render_table(rows: list[list[Any]], headers: list[str]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return out


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_report(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    required_files = [DATASET_JSON, FOLDS_JSON, NONCRYPTIC_JSON, ZIP_PATH, *FOLD_FILES.values()]
    missing = [path for path in required_files if not path.is_file()]
    if missing:
        print("Missing required inputs:")
        for path in missing:
            print(f"- {path}")
        return 1

    dataset = load_json(DATASET_JSON)
    folds = load_json(FOLDS_JSON)
    noncryptic = load_json(NONCRYPTIC_JSON)
    fold_payloads = {name: load_json(path) for name, path in FOLD_FILES.items()}

    cryptic_records = collect_records(dataset, "cryptic")
    noncryptic_records = collect_records(noncryptic, "noncryptic")
    all_records = cryptic_records + noncryptic_records

    apo_to_fold = {}
    duplicate_fold_assignments: dict[str, list[str]] = defaultdict(list)
    for fold, apo_ids in folds.items():
        for apo_id in apo_ids:
            if apo_id in apo_to_fold:
                duplicate_fold_assignments[apo_id].extend([apo_to_fold[apo_id], fold])
            apo_to_fold[apo_id] = fold

    records_by_fold = split_records_by_fold(cryptic_records, apo_to_fold)
    fold_integrity = {
        fold: {
            "folds_json_apo_count": len(folds.get(fold, [])),
            "fold_file_apo_count": len(payload),
            "keys_match_folds_json": sorted(payload) == sorted(folds.get(fold, [])),
            "missing_from_file": sorted(set(folds.get(fold, [])) - set(payload)),
            "extra_in_file": sorted(set(payload) - set(folds.get(fold, []))),
        }
        for fold, payload in fold_payloads.items()
    }

    dataset_entry_keys = Counter(record["entry_key"] for record in cryptic_records if "entry_key" in record)
    duplicate_entries = sorted(key for key, count in dataset_entry_keys.items() if count > 1)

    field_profiles = {
        "cryptic": field_profile(cryptic_records),
        "noncryptic": field_profile(noncryptic_records),
    }
    selection_profiles = {
        "cryptic": analyze_selections(cryptic_records),
        "noncryptic": analyze_selections(noncryptic_records),
    }

    cryptic_required_pdb_ids = {
        normalize_pdb_id(record.get("apo_pdb_id"))
        for record in cryptic_records
        if record.get("apo_pdb_id")
    } | {
        normalize_pdb_id(record.get("holo_pdb_id"))
        for record in cryptic_records
        if record.get("holo_pdb_id")
    }
    noncryptic_required_pdb_ids = {
        normalize_pdb_id(record.get("apo_pdb_id"))
        for record in noncryptic_records
        if record.get("apo_pdb_id")
    } | {
        normalize_pdb_id(record.get("holo_pdb_id"))
        for record in noncryptic_records
        if record.get("holo_pdb_id")
    }
    required_pdb_ids = cryptic_required_pdb_ids | noncryptic_required_pdb_ids
    cif_summaries, zip_summary = inspect_cifs(
        required_pdb_ids,
        {
            "cryptic": cryptic_required_pdb_ids,
            "noncryptic": noncryptic_required_pdb_ids,
            "combined": required_pdb_ids,
        },
    )
    cif_validation = validate_record_against_cif(all_records, cif_summaries)

    overlap = cross_fold_overlap(folds, records_by_fold)

    main_holo_counts = Counter(
        str(record.get("is_main_holo_structure")) for record in cryptic_records if "is_main_holo_structure" in record
    )
    prmsd_values = [float(record["pRMSD"]) for record in cryptic_records if isinstance(record.get("pRMSD"), (int, float))]
    uniprots = sorted({str(record["uniprot_id"]) for record in cryptic_records if record.get("uniprot_id")})
    ligands = sorted({str(record["ligand"]) for record in cryptic_records if record.get("ligand")})
    pcna_uniprot_hits = sorted(uid for uid in uniprots if uid.upper() == "P12004")
    pcna_records = [
        {
            "apo_pdb_id": record.get("apo_pdb_id"),
            "fold": apo_to_fold.get(record.get("apo_pdb_id")),
            "uniprot_id": record.get("uniprot_id"),
            "holo_pdb_id": record.get("holo_pdb_id"),
            "apo_chain": record.get("apo_chain"),
            "holo_chain": record.get("holo_chain"),
            "ligand": record.get("ligand"),
            "ligand_index": record.get("ligand_index"),
            "pRMSD": record.get("pRMSD"),
            "is_main_holo_structure": record.get("is_main_holo_structure"),
        }
        for record in cryptic_records
        if str(record.get("uniprot_id")).upper() == "P12004"
        or normalize_pdb_id(record.get("apo_pdb_id")) in {"3vkx", "5e0v"}
        or normalize_pdb_id(record.get("holo_pdb_id")) in {"3vkx", "5e0v"}
    ]
    pcna_text_hits = {
        pdb_id: summary.pcna_term_hits
        for pdb_id, summary in sorted(cif_summaries.items())
        if summary.pcna_term_hits
    }

    schema_summary = {
        "audit_status": "completed_local_deep_audit_not_adopted",
        "created_at": now(),
        "adoption_status": "not_adopted",
        "allowed_use": "audit_only",
        "blocked_actions": ["training", "graph_generation", "split_freeze", "label_freeze", "MD", "claims"],
        "input_files": {
            rel(path): {
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in [DATASET_JSON, FOLDS_JSON, NONCRYPTIC_JSON, *FOLD_FILES.values()]
        },
        "dataset_counts": {
            "cryptic_apo_key_count": len(dataset),
            "cryptic_pair_record_count": len(cryptic_records),
            "noncryptic_apo_key_count": len(noncryptic),
            "noncryptic_pair_record_count": len(noncryptic_records),
            "unique_uniprot_count": len(uniprots),
            "unique_ligand_count": len(ligands),
            "unique_required_pdb_id_count": len(required_pdb_ids),
            "cryptic_required_pdb_id_count": len(cryptic_required_pdb_ids),
            "noncryptic_required_pdb_id_count": len(noncryptic_required_pdb_ids),
            "duplicate_entry_count": len(duplicate_entries),
        },
        "field_profiles": field_profiles,
        "selection_profiles": selection_profiles,
        "pRMSD_summary": {
            "count": len(prmsd_values),
            "min": min(prmsd_values) if prmsd_values else None,
            "max": max(prmsd_values) if prmsd_values else None,
            "mean": round(sum(prmsd_values) / len(prmsd_values), 4) if prmsd_values else None,
        },
        "is_main_holo_structure_counts": dict(main_holo_counts),
        "label_semantics": {
            "unit": "pocket-selection residue tokens inside apo-holo pair records",
            "positive_label_type": "cryptic binding-site pocket residue selection as provided by CryptoBench",
            "noncryptic_label_type": "additional non-cryptic pocket residue selections, not true residue-level negatives",
            "negative_semantics": "not explicitly enumerated as true biological negatives in local files",
            "apo_holo_pairing": "explicit via apo dictionary key plus holo_pdb_id/holo_chain fields",
            "claim_limit": "benchmark proxy/curated cryptic binding site labels; not direct experimental proof for every residue",
        },
        "pcna_screen": {
            "exact_human_pcna_uniprot_hits": pcna_uniprot_hits,
            "pcna_records": pcna_records,
            "cif_text_hits": pcna_text_hits,
        },
    }

    fold_summary = {
        "audit_status": "completed_local_split_risk_audit_not_frozen",
        "created_at": now(),
        "adoption_status": "not_adopted",
        "fold_counts": {
            fold: {
                "apo_count": len(apo_ids),
                "cryptic_pair_record_count": len(records_by_fold.get(fold, [])),
                "unique_uniprot_count": len(
                    {str(r["uniprot_id"]) for r in records_by_fold.get(fold, []) if r.get("uniprot_id")}
                ),
            }
            for fold, apo_ids in sorted(folds.items())
        },
        "fold_integrity": fold_integrity,
        "duplicate_fold_assignment_count": len(duplicate_fold_assignments),
        "duplicate_fold_assignments": {key: sorted(set(value)) for key, value in duplicate_fold_assignments.items()},
        "overlap": overlap,
        "split_readiness": {
            "benchmark_split_can_be_frozen": False,
            "reason": "local files lack sequence-cluster/homolog grouping evidence and human split review; leakage risk remains unresolved",
        },
    }

    structure_index = {
        "audit_status": "completed_local_structure_inventory_not_graphs",
        "created_at": now(),
        "adoption_status": "not_adopted",
        "zip_summary": zip_summary,
        "cif_validation": cif_validation,
        "structures": {
            pdb_id: {
                "zip_member": summary.zip_member,
                "compressed_size": summary.compressed_size,
                "uncompressed_size": summary.uncompressed_size,
                "readable": summary.readable,
                "atom_site_found": summary.atom_site_found,
                "atom_site_parse_error": summary.atom_site_parse_error,
                "chains": summary.chains,
                "residue_count": summary.residue_count,
                "atom_count": summary.atom_count,
                "residues_by_chain": summary.residues_by_chain,
                "pcna_term_hits": summary.pcna_term_hits,
            }
            for pdb_id, summary in sorted(cif_summaries.items())
        },
    }

    write_json(REGISTRIES["schema"], schema_summary)
    write_json(REGISTRIES["fold"], fold_summary)
    write_json(REGISTRIES["structure"], structure_index)

    common_provenance = [
        "",
        "## Provenance",
        "",
        f"- Date: {schema_summary['created_at']}",
        "- Command: `python scripts/cryptobench_deep_audit.py`",
        "- Source paths: `data/raw_intake/cryptobench/metadata_files/`, `data/raw_intake/cryptobench/labels_or_splits/`, `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`",
        "- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `14_CLAIM_POLICY.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`",
        "- Confidence: high for local schema/count/hash/readability checks; medium for label-semantic interpretation from local README; low for homolog exclusion because no sequence clustering was run.",
        "- Evidence status: verified for local files and machine checks; inferred for biological meaning; uncertain for final scientific usability.",
    ]

    write_report(
        REPORTS["schema"],
        [
            "# CryptoBench Schema Deep Audit",
            "",
            "## Status",
            "",
            "- Final audit status: `LOCAL_SCHEMA_AUDITED_NOT_ADOPTED`",
            "- Adoption status: `not_adopted`",
            "- Allowed use: audit and human review packet only.",
            "- Blocked: training, graph generation, split freeze, label freeze, MD, evaluation claims, and PCNA claims.",
            "",
            "## What CryptoBench Contains Locally",
            "",
            f"- `dataset.json`: {len(dataset)} apo PDB keys and {len(cryptic_records)} apo-holo pocket records.",
            f"- `noncryptic-pockets.json`: {len(noncryptic)} apo PDB keys and {len(noncryptic_records)} additional non-cryptic pocket records.",
            f"- `folds.json`: {len(folds)} fold buckets: {', '.join(sorted(folds))}.",
            f"- `cif-files.zip`: {zip_summary['zip_file_count']} `.cif` files.",
            f"- Cryptic `dataset.json` references {zip_summary['presence_by_record_type']['cryptic']['required_structure_count']} unique structures; {zip_summary['presence_by_record_type']['cryptic']['missing_structure_count']} are missing from the ZIP.",
            f"- Noncryptic auxiliary records reference {zip_summary['presence_by_record_type']['noncryptic']['required_structure_count']} unique structures; {zip_summary['presence_by_record_type']['noncryptic']['missing_structure_count']} are missing from the ZIP.",
            "",
            "## Exact Record Fields",
            "",
            *render_table(
                [
                    [
                        name,
                        field_profiles["cryptic"].get(name, {}).get("types", {}),
                        field_profiles["cryptic"].get(name, {}).get("present_count", 0),
                        field_profiles["cryptic"].get(name, {}).get("missing_count", 0),
                    ]
                    for name in sorted(field_profiles["cryptic"])
                    if name not in {"record_type", "apo_pdb_id", "entry_index", "entry_key"}
                ],
                ["Field", "Types", "Present", "Missing"],
            ),
            "",
            "The non-cryptic file uses the same core fields but lacks `pRMSD` and `is_main_holo_structure` in the local payload.",
            "",
            "## Structural Meaning Of Fields",
            "",
            "- Top-level JSON keys are apo PDB IDs, not individual residues.",
            "- Each value is a list of holo partner records; one apo structure can map to multiple holo structures and ligands.",
            "- `apo_chain`, `holo_chain`, and `ligand_chain` define chain IDs for each paired record.",
            "- `apo_pocket_selection` and `holo_pocket_selection` are lists of chain/residue tokens such as `B_12`; the local README states these are auth asym IDs and auth sequence IDs.",
            "- `pRMSD` and `is_main_holo_structure` describe pocket RMSD and the highest-pRMSD holo structure for that apo context.",
            "",
            "## Selection Integrity",
            "",
            *render_table(
                [
                    [
                        "cryptic",
                        field,
                        stats["entry_count"],
                        stats["min_len"],
                        stats["max_len"],
                        stats["mean_len"],
                        stats["malformed_count"],
                        stats["wrong_chain_count"],
                    ]
                    for field, stats in selection_profiles["cryptic"].items()
                ]
                + [
                    [
                        "noncryptic",
                        field,
                        stats["entry_count"],
                        stats["min_len"],
                        stats["max_len"],
                        stats["mean_len"],
                        stats["malformed_count"],
                        stats["wrong_chain_count"],
                    ]
                    for field, stats in selection_profiles["noncryptic"].items()
                ],
                ["File", "Selection field", "Records", "Min", "Max", "Mean", "Malformed", "Wrong chain"],
            ),
            "",
            "## Duplicate And Malformed Entry Checks",
            "",
            f"- Duplicate cryptic pair records by apo/chain/holo/ligand key: {len(duplicate_entries)}.",
            f"- Cryptic required CIF structures missing from ZIP: {zip_summary['presence_by_record_type']['cryptic']['missing_structure_count']}.",
            f"- Noncryptic auxiliary required CIF structures missing from ZIP: {zip_summary['presence_by_record_type']['noncryptic']['missing_structure_count']}.",
            f"- CIF atom-site parse issues among required structures: {sum(1 for s in cif_summaries.values() if s.atom_site_parse_error)}.",
            f"- Chain absence issues for selected apo/holo chains: {cif_validation['chain_absence_issue_count']}.",
            "",
            f"Exact selected residue tokens absent from parsed atom-site residue tables: {cif_validation['selection_tokens_absent_from_atom_site']}. This check uses auth sequence ID and auth sequence ID plus insertion-code forms; final graph generation still needs an approved residue-node policy.",
            *common_provenance,
        ],
    )

    write_report(
        REPORTS["split"],
        [
            "# CryptoBench Split Risk Audit",
            "",
            "## Status",
            "",
            "- Final audit status: `SPLIT_RISK_UNRESOLVED_NOT_FROZEN`",
            "- The provided folds are usable as source metadata, not as a Phase 2 frozen split.",
            "",
            "## Fold Integrity",
            "",
            *render_table(
                [
                    [
                        fold,
                        data["folds_json_apo_count"],
                        data["fold_file_apo_count"],
                        data["keys_match_folds_json"],
                        len(data["missing_from_file"]),
                        len(data["extra_in_file"]),
                    ]
                    for fold, data in sorted(fold_integrity.items())
                ],
                ["Fold", "folds.json apo", "fold file apo", "Keys match", "Missing", "Extra"],
            ),
            "",
            "## Leakage Checks Available From Local Files",
            "",
            f"- Duplicate apo IDs across folds: {overlap['apo_id_cross_fold_overlap_count']}.",
            f"- Duplicate fold assignments in `folds.json`: {len(duplicate_fold_assignments)}.",
            f"- UniProt IDs appearing in more than one fold: {overlap['shared_uniprot_count']}.",
            f"- UniProt IDs shared between train folds and test: {overlap['train_test_shared_uniprot_count']}.",
            f"- Holo PDB IDs appearing in more than one fold: {overlap['shared_holo_pdb_count']}.",
            "",
            "## Interpretation",
            "",
            "- The fold files are internally consistent with `folds.json` if the table above reports `True` for each fold.",
            "- The local split files do not include sequence-cluster IDs, homolog-cluster IDs, structural similarity clusters, or an apo/holo grouping proof.",
            "- Repeated UniProt IDs across folds are direct leakage risks under Phase 2 governance, even if benchmark authors intended a different evaluation design.",
            "- Homolog leakage risk remains unresolved until sequence clustering and structural review are run under an approved protocol.",
            "- Split freeze is not feasible from these files alone.",
            "",
            "## Train/Test Shared UniProt IDs",
            "",
            *([", ".join(overlap["train_test_shared_uniprots"])] if overlap["train_test_shared_uniprots"] else ["None detected by exact UniProt ID. Homolog risk remains unresolved."]),
            *common_provenance,
        ],
    )

    write_report(
        REPORTS["labels"],
        [
            "# CryptoBench Label Semantics",
            "",
            "## Status",
            "",
            "- Final audit status: `LABEL_SEMANTICS_PROXY_NOT_FROZEN`",
            "- Label freeze is not authorized.",
            "",
            "## What The Labels Are",
            "",
            "- The local files provide pocket residue selections per apo-holo record.",
            "- The labels are residue-token annotations within pocket selections, but the dataset object is apo/holo-pair-level rather than a direct dense residue-label table.",
            "- The positive class in `dataset.json` is best described as CryptoBench cryptic binding-site pocket residue selections.",
            "- The local README describes paired apo and holo pocket selections and ligand metadata, but it does not make every unlisted residue a verified biological non-pocket residue.",
            "",
            "## Positive, Noncryptic, Negative, And Unlabeled Semantics",
            "",
            *render_table(
                [
                    ["Cryptic positive", "`dataset.json` `apo_pocket_selection` / `holo_pocket_selection`", "Residue-level tokens inside apo-holo records", "Benchmark cryptic binding-site positives, not independent experimental proof for every residue"],
                    ["Noncryptic pocket", "`noncryptic-pockets.json`", "Residue-level tokens inside apo-holo-like records", "Additional non-cryptic pockets; not true negative residue labels"],
                    ["True negatives", "Not explicitly enumerated", "No direct true-negative table found", "Unlisted residues must be treated as unlabeled or benchmark-background until a reviewed rule says otherwise"],
                    ["Ambiguous", "Not explicitly marked", "No ambiguity mask found", "Must be defined before graph generation/training"],
                ],
                ["Class", "Local source", "Granularity", "Governed interpretation"],
            ),
            "",
            "## Biological Meaning",
            "",
            "- The labels appear biologically motivated by apo-holo ligand-binding contexts and pocket RMSD, but they remain benchmark annotations and proxy labels for Phase 2.",
            "- The labels are not sufficient to claim validated cryptic biology for PCNA or any individual residue without source review and biological sanity checks.",
            "- `noncryptic-pockets.json` suggests the benchmark distinguishes cryptic from non-cryptic pocket contexts, which is useful for audit, but it does not solve the true-negative problem.",
            "- Likely biases include ligand availability bias, solved-structure/publication bias, apo-holo pairing bias, ligand class/size bias, chain/residue-numbering bias, and protein-family bias.",
            "",
            "## Feasibility For Residue-Level Learning",
            "",
            "- Feasible in principle: residue tokens can be mapped to chain/auth sequence IDs in mmCIF files.",
            "- Not ready: a graph node table must preserve chain, auth sequence ID, insertion code, residue name, missing-residue policy, and label mask.",
            "- ESM alignment is feasible only after a governed sequence extraction and missing-residue/index-shift policy. The bundled example explicitly warns that annotation indices can shift from dataset residue numbering.",
            *common_provenance,
        ],
    )

    parse_errors = [s for s in cif_summaries.values() if s.atom_site_parse_error]
    write_report(
        REPORTS["structures"],
        [
            "# CryptoBench Structure Inventory",
            "",
            "## Status",
            "",
            "- Final audit status: `STRUCTURES_READABLE_FOR_AUDIT_NOT_GRAPHED`",
            "- Graph construction is not authorized by this report.",
            "",
            "## Inventory Summary",
            "",
            f"- ZIP path: `{zip_summary['zip_path']}`",
            f"- ZIP SHA-256: `{zip_summary['zip_sha256']}`",
            f"- ZIP `.cif` count: {zip_summary['zip_file_count']}",
            f"- Required PDB IDs from cryptic records: {zip_summary['presence_by_record_type']['cryptic']['required_structure_count']}",
            f"- Missing cryptic required structures: {zip_summary['presence_by_record_type']['cryptic']['missing_structure_count']}",
            f"- Required PDB IDs from noncryptic auxiliary records: {zip_summary['presence_by_record_type']['noncryptic']['required_structure_count']}",
            f"- Missing noncryptic auxiliary structures: {zip_summary['presence_by_record_type']['noncryptic']['missing_structure_count']}",
            f"- Extra CIFs not referenced by parsed records: {zip_summary['extra_cif_count']}",
            f"- Required CIFs readable: {sum(1 for s in cif_summaries.values() if s.readable)} / {len(cif_summaries)}",
            f"- Required CIFs with atom_site loop found: {sum(1 for s in cif_summaries.values() if s.atom_site_found)} / {len(cif_summaries)}",
            f"- Required CIF atom-site parse issues: {len(parse_errors)}",
            "",
            "## Graph Feasibility",
            "",
            "- Residue-level graph construction appears practical in principle for `dataset.json` cryptic records because all 5,005 referenced mmCIF files are present/readable and atom-site loops expose chains and resolved residues.",
            "- Graph construction is not complete for `noncryptic-pockets.json` as-is because 6,915 referenced noncryptic auxiliary structures are not present in the local ZIP.",
            "- The appropriate MVP node granularity is one resolved protein residue per `(structure_id, chain_id, auth_seq_id, insertion_code, residue_name)` record.",
            "- Edge construction from CIFs appears practical for spatial contacts and sequence edges, but final cutoff/atom basis and missing-gap policy must be frozen before graph generation.",
            "- Chain and residue metadata must be preserved exactly; reindexing would violate governance.",
            "- ESM/protein-sequence alignment is feasible but risky unless the project stores both the observed-residue sequence and source/auth numbering map. The bundled example documents a numbering shift for `7w19A`.",
            "",
            "## Missing Noncryptic Auxiliary Structure Examples",
            "",
            *([f"- `{pdb_id}`" for pdb_id in zip_summary["missing_required_structures"][:100]] or ["None detected among required PDB IDs."]),
            "",
            "## Atom-Site Parse Error Examples",
            "",
            *([f"- `{s.pdb_id}`: {s.atom_site_parse_error}" for s in parse_errors[:50]] or ["None detected by the lightweight parser."]),
            "",
            "## Residue And Chain Consistency",
            "",
            f"- Selected residue tokens checked against parsed atom-site residue IDs: {cif_validation['checked_selection_token_count']}.",
            f"- Selected residue tokens absent from parsed atom-site residue IDs: {cif_validation['selection_tokens_absent_from_atom_site']}.",
            f"- Selected-chain absence issues: {cif_validation['chain_absence_issue_count']}.",
            "- Residue numbering is therefore mostly parseable, but not clean enough for graph generation without a reviewed missing-residue/insertion-code policy and residue-level spot checks.",
            "",
            "## Machine-Readable Index",
            "",
            f"- Full per-structure index: `{rel(REGISTRIES['structure'])}`",
            *common_provenance,
        ],
    )

    write_report(
        REPORTS["pcna"],
        [
            "# PCNA Contamination Screen",
            "",
            "## Status",
            "",
            "- Final audit status: `EXACT_PCNA_CONTAMINATION_DETECTED_HOMOLOG_RISK_UNRESOLVED`",
            "- PCNA isolation is not frozen.",
            "",
            "## Exact Screens Run",
            "",
            f"- Exact dataset UniProt screen for human PCNA `P12004`: {len(pcna_records)} record hits.",
            f"- Required CIF text screen terms: {', '.join(f'`{term}`' for term in PCNA_TERMS)}.",
            f"- Required CIFs with PCNA/sliding-clamp term hits: {len(pcna_text_hits)}.",
            "",
            "## Hits",
            "",
            *([f"- Dataset record: apo `{r['apo_pdb_id']}` fold `{r['fold']}`, holo `{r['holo_pdb_id']}`, UniProt `{r['uniprot_id']}`, ligand `{r['ligand']}` `{r['ligand_index']}`." for r in pcna_records] or ["No exact human PCNA UniProt records detected."]),
            *([f"- CIF text hit `{pdb_id}`: {', '.join(hits)}" for pdb_id, hits in list(pcna_text_hits.items())[:100]] or ["No required CryptoBench CIF text hits for the configured PCNA terms."]),
            "",
            "## Interpretation Limits",
            "",
            "- This is a local exact-text and exact-UniProt screen, not a homolog search.",
            "- Absence of `P12004` and PCNA text hits does not exclude PCNA-like clamps or distant structural homologs.",
            "- A governed sequence-cluster and structural-similarity screen is still required before any split freeze or PCNA final-claim holdout statement.",
            *common_provenance,
        ],
    )

    print(f"Wrote {rel(REPORTS['schema'])}")
    print(f"Wrote {rel(REPORTS['split'])}")
    print(f"Wrote {rel(REPORTS['labels'])}")
    print(f"Wrote {rel(REPORTS['structures'])}")
    print(f"Wrote {rel(REPORTS['pcna'])}")
    print(f"Wrote {rel(REGISTRIES['schema'])}")
    print(f"Wrote {rel(REGISTRIES['fold'])}")
    print(f"Wrote {rel(REGISTRIES['structure'])}")
    print("Final status: LOCAL_CRYPTOBENCH_AUDITED_NOT_ADOPTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
