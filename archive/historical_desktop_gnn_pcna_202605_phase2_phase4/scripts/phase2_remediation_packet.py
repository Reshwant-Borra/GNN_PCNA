#!/usr/bin/env python3
"""Build Phase 2 CryptoBench remediation and auxiliary-intake handoff packet.

This script writes planning/audit artifacts only. It does not freeze splits or
labels, generate graphs, train, run MD, or make scientific claims.
"""

from __future__ import annotations

import json
import re
import zipfile
from collections import Counter, defaultdict
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
SCHEMA_SUMMARY = REGISTRY_DIR / "cryptobench_schema_summary.json"
FOLD_SUMMARY = REGISTRY_DIR / "cryptobench_fold_summary.json"
STRUCTURE_INDEX = REGISTRY_DIR / "cryptobench_structure_index.json"
DATASET_INVENTORY = REGISTRY_DIR / "dataset_inventory.json"

REPORTS = {
    "adoption": REPORT_DIR / "cryptobench_adoption_decision.md",
    "pcna_policy": REPORT_DIR / "pcna_isolation_policy.md",
    "leakage": REPORT_DIR / "cryptobench_leakage_remediation.md",
    "label_risks": REPORT_DIR / "label_supervision_risks.md",
    "label_policy": REPORT_DIR / "proposed_label_policy.md",
    "residue_failures": REPORT_DIR / "residue_mapping_failure_analysis.md",
    "split_strategy": REPORT_DIR / "proposed_phase2_split_strategy.md",
    "cleaned_registry": REPORT_DIR / "cryptobench_candidate_cleaned_registry.md",
    "aux_audit": REPORT_DIR / "auxiliary_dataset_audit.md",
    "role_table": REPORT_DIR / "benchmark_role_classification.md",
    "acquisition": REPORT_DIR / "auxiliary_acquisition_status_summary.md",
    "footprint": REPORT_DIR / "dataset_footprint_summary.md",
    "handoff": REPORT_DIR / "phase2_claude_code_handoff.md",
}

REGISTRIES = {
    "homolog_risks": REGISTRY_DIR / "potential_homolog_risks.json",
    "residue_failures": REGISTRY_DIR / "residue_mapping_failures.json",
    "cleaned_registry": REGISTRY_DIR / "cryptobench_candidate_cleaned_registry.json",
    "aux_roles": REGISTRY_DIR / "auxiliary_dataset_role_summary.json",
}

SELECTION_RE = re.compile(r"^(?P<chain>.+)_(?P<residue>-?\d+[A-Za-z]?)$")


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_report(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return lines


def collect_records(dataset: dict[str, Any], record_type: str, apo_to_fold: dict[str, str]) -> list[dict[str, Any]]:
    records = []
    for apo_id, entries in dataset.items():
        if not isinstance(entries, list):
            continue
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            row = dict(entry)
            row["record_type"] = record_type
            row["apo_pdb_id"] = apo_id
            row["entry_index"] = i
            row["fold"] = apo_to_fold.get(apo_id, "unassigned")
            row["pair_key"] = "|".join(
                [
                    apo_id,
                    str(row.get("apo_chain", "")),
                    str(row.get("holo_pdb_id", "")),
                    str(row.get("holo_chain", "")),
                    str(row.get("ligand", "")),
                    str(row.get("ligand_index", "")),
                    str(row.get("ligand_chain", "")),
                ]
            )
            records.append(row)
    return records


def parse_selection(token: Any) -> tuple[str | None, str | None]:
    if not isinstance(token, str):
        return None, None
    match = SELECTION_RE.match(token)
    if not match:
        return None, None
    return match.group("chain"), match.group("residue")


def parse_atom_site_tokens(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    columns: list[str] | None = None
    i = 0
    while i < len(lines):
        if lines[i].strip() == "loop_":
            j = i + 1
            current = []
            while j < len(lines) and lines[j].strip().startswith("_"):
                current.append(lines[j].strip().split()[0])
                j += 1
            if any(col.startswith("_atom_site.") for col in current):
                columns = current
                i = j
                break
        i += 1
    if not columns:
        return {"chains": {}, "all_auth_tokens": set(), "all_label_tokens": set()}

    idx = {name: ix for ix, name in enumerate(columns)}
    required = ["_atom_site.group_PDB", "_atom_site.label_comp_id", "_atom_site.auth_asym_id", "_atom_site.auth_seq_id"]
    if any(name not in idx for name in required):
        return {"chains": {}, "all_auth_tokens": set(), "all_label_tokens": set()}

    label_chain_idx = idx.get("_atom_site.label_asym_id")
    label_seq_idx = idx.get("_atom_site.label_seq_id")
    ins_idx = idx.get("_atom_site.pdbx_PDB_ins_code")
    chains: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"auth": set(), "label": set()})
    all_auth: set[str] = set()
    all_label: set[str] = set()
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped == "#" or stripped == "loop_" or stripped.startswith("_") or stripped.startswith("data_"):
            break
        parts = stripped.split()
        if len(parts) < len(columns):
            break
        if parts[idx["_atom_site.group_PDB"]] == "ATOM":
            auth_chain = parts[idx["_atom_site.auth_asym_id"]]
            auth_seq = parts[idx["_atom_site.auth_seq_id"]]
            ins = parts[ins_idx] if ins_idx is not None else "?"
            auth_tokens = {auth_seq}
            if ins not in {"?", ".", ""}:
                auth_tokens.add(f"{auth_seq}{ins}")
            chains[auth_chain]["auth"].update(auth_tokens)
            all_auth.update(auth_tokens)
            if label_chain_idx is not None and label_seq_idx is not None:
                label_chain = parts[label_chain_idx]
                label_seq = parts[label_seq_idx]
                if label_seq not in {"?", "."}:
                    chains[label_chain]["label"].add(label_seq)
                    all_label.add(label_seq)
        i += 1
    return {"chains": chains, "all_auth_tokens": all_auth, "all_label_tokens": all_label}


def residue_mapping_failures(records: list[dict[str, Any]]) -> dict[str, Any]:
    required_ids = sorted(
        {
            str(record.get("apo_pdb_id", "")).lower()
            for record in records
            if record.get("apo_pdb_id")
        }
        | {
            str(record.get("holo_pdb_id", "")).lower()
            for record in records
            if record.get("holo_pdb_id")
        }
    )
    failures = []
    missing_cif: Counter[str] = Counter()
    present_cache: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(ZIP_PATH, "r") as archive:
        members = {
            Path(info.filename).stem.lower(): info.filename
            for info in archive.infolist()
            if info.filename.endswith(".cif")
        }
        for pdb_id in required_ids:
            member = members.get(pdb_id)
            if member:
                text = archive.read(member).decode("utf-8", errors="replace")
                present_cache[pdb_id] = parse_atom_site_tokens(text)

    checked = 0
    for record in records:
        for role, pdb_id_raw, field in [
            ("apo", record.get("apo_pdb_id"), "apo_pocket_selection"),
            ("holo", record.get("holo_pdb_id"), "holo_pocket_selection"),
        ]:
            pdb_id = str(pdb_id_raw).lower()
            parsed = present_cache.get(pdb_id)
            selections = record.get(field)
            if not isinstance(selections, list):
                continue
            if not parsed:
                missing_cif[pdb_id] += len(selections)
                continue
            for token in selections:
                chain, residue = parse_selection(token)
                if chain is None or residue is None:
                    continue
                checked += 1
                chain_info = parsed["chains"].get(chain)
                if chain_info and residue in chain_info["auth"]:
                    continue
                if chain_info and residue in chain_info["label"]:
                    reason = "matches_label_seq_id_not_auth_seq_id"
                elif residue in parsed["all_auth_tokens"]:
                    reason = "residue_token_exists_on_other_chain"
                elif residue in parsed["all_label_tokens"]:
                    reason = "label_seq_id_exists_on_other_chain"
                elif not chain_info:
                    reason = "chain_absent_from_atom_site"
                else:
                    reason = "residue_token_absent_from_atom_site"
                failures.append(
                    {
                        "record_type": record["record_type"],
                        "fold": record.get("fold"),
                        "role": role,
                        "pdb_id": pdb_id,
                        "apo_pdb_id": record.get("apo_pdb_id"),
                        "holo_pdb_id": record.get("holo_pdb_id"),
                        "uniprot_id": record.get("uniprot_id"),
                        "chain": chain,
                        "residue_token": residue,
                        "selection_token": token,
                        "reason": reason,
                    }
                )

    return {
        "created_at": now(),
        "status": "residue_mapping_failures_audited_not_remediated",
        "checked_selection_tokens_with_present_cifs": checked,
        "failure_count": len(failures),
        "failure_reason_counts": dict(Counter(item["reason"] for item in failures)),
        "failure_record_type_counts": dict(Counter(item["record_type"] for item in failures)),
        "missing_cif_selection_token_count": sum(missing_cif.values()),
        "missing_cif_structure_count": len(missing_cif),
        "missing_cif_examples": sorted(missing_cif)[:100],
        "failures": failures,
    }


def repeated_holo_risks(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_holo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_holo[str(record.get("holo_pdb_id", "")).lower()].append(record)
    risks = {}
    for holo_id, rows in sorted(by_holo.items()):
        folds = sorted({row.get("fold", "unassigned") for row in rows})
        if len(folds) > 1:
            risks[holo_id] = [
                {
                    "fold": row.get("fold"),
                    "apo_pdb_id": row.get("apo_pdb_id"),
                    "apo_chain": row.get("apo_chain"),
                    "holo_chain": row.get("holo_chain"),
                    "uniprot_id": row.get("uniprot_id"),
                    "ligand": row.get("ligand"),
                    "ligand_index": row.get("ligand_index"),
                }
                for row in rows
            ]
    return risks


def candidate_cleaned_registry(
    cryptic_records: list[dict[str, Any]],
    residue_failures: dict[str, Any],
    repeated_holos: dict[str, Any],
    pcna_records: list[dict[str, Any]],
) -> dict[str, Any]:
    pcna_apo_ids = {str(row["apo_pdb_id"]).lower() for row in pcna_records}
    pcna_holo_ids = {str(row["holo_pdb_id"]).lower() for row in pcna_records}
    repeated_holo_ids = set(repeated_holos)
    failure_pair_keys = set()
    for fail in residue_failures["failures"]:
        if fail["record_type"] == "cryptic":
            failure_pair_keys.add((fail["apo_pdb_id"], fail["holo_pdb_id"]))

    exclusions = []
    holdouts = []
    for record in cryptic_records:
        apo_id = str(record["apo_pdb_id"]).lower()
        holo_id = str(record.get("holo_pdb_id", "")).lower()
        reasons = []
        if apo_id in pcna_apo_ids or holo_id in pcna_holo_ids:
            reasons.append("PCNA_P12004_exact_contamination")
        if holo_id in repeated_holo_ids:
            reasons.append("holo_pdb_repeats_across_official_folds")
        if (record["apo_pdb_id"], record.get("holo_pdb_id")) in failure_pair_keys:
            reasons.append("selected_residue_mapping_failure_present")
        if reasons:
            exclusions.append(
                {
                    "apo_pdb_id": record["apo_pdb_id"],
                    "holo_pdb_id": record.get("holo_pdb_id"),
                    "fold": record.get("fold"),
                    "uniprot_id": record.get("uniprot_id"),
                    "reasons": sorted(set(reasons)),
                    "recommendation": "exclude_or_hold_out_pending_human_review",
                }
            )
        if apo_id in pcna_apo_ids or holo_id in pcna_holo_ids:
            holdouts.append(
                {
                    "holdout_type": "pcna_external_blind_or_positive_control_only",
                    "apo_pdb_id": record["apo_pdb_id"],
                    "holo_pdb_id": record.get("holo_pdb_id"),
                    "fold": record.get("fold"),
                    "uniprot_id": record.get("uniprot_id"),
                    "allowed_use": "not_training_not_model_selection",
                }
            )

    return {
        "created_at": now(),
        "status": "candidate_registry_not_adopted_not_frozen",
        "source": "CryptoBench cryptic dataset.json only",
        "total_cryptic_records": len(cryptic_records),
        "candidate_adoption_recommendation": "cryptic_only_benchmark_candidate_with_exclusions_and_new_homolog_aware_split",
        "excluded_or_review_required_record_count": len(exclusions),
        "holdout_record_count": len(holdouts),
        "exclusions_or_review_required": exclusions,
        "holdouts": holdouts,
        "noncryptic_auxiliary_policy": "do_not_use_for_training_until_missing_structures_are_acquired_or_records_are_subsetted_and_audited",
        "not_authorized": ["split_freeze", "label_freeze", "graph_generation", "training", "MD", "claims"],
    }


def inventory_roles(inventory: dict[str, Any]) -> dict[str, Any]:
    role_map = {
        "cryptobench": {
            "role": "primary benchmark candidate after remediation",
            "keep": "yes_with_exclusions_pending_human_review",
            "supervision": "proxy cryptic pocket selections",
            "limitation": "not true negatives; PCNA contamination; split redesign required",
        },
        "biolip": {
            "role": "auxiliary ligand-contact/proxy context",
            "keep": "yes_linked_only_until_terms_and_schema_review",
            "supervision": "ligand contacts if later acquired",
            "limitation": "not cryptic-pocket truth",
        },
        "scpdb": {
            "role": "auxiliary binding-pocket/proxy source",
            "keep": "maybe_terms_and_bulk_size_unresolved",
            "supervision": "binding pocket/protein-ligand records if later acquired",
            "limitation": "not cryptic-pocket truth; licensing/bulk unresolved",
        },
        "asd": {
            "role": "allosteric context/reference",
            "keep": "yes_as_context_not_training_labels",
            "supervision": "allosteric annotations only after entry-level audit",
            "limitation": "not PCNA cryptic-pocket supervision by default",
        },
        "pocketminer": {
            "role": "baseline/method reference",
            "keep": "yes_for_baseline_review",
            "supervision": "method outputs only; not labels",
            "limitation": "overlap/leakage with CryptoBench must be audited",
        },
        "baseline_tools": {
            "role": "fpocket/P2Rank baseline tooling metadata",
            "keep": "yes_for_baseline_planning",
            "supervision": "tool predictions only",
            "limitation": "installation/output schemas not verified",
        },
        "biogrid": {
            "role": "targeted PCNA interaction context",
            "keep": "yes_context_only",
            "supervision": "interaction metadata only after API/license review",
            "limitation": "not structural pocket labels",
        },
        "string": {
            "role": "targeted PCNA functional association context",
            "keep": "yes_context_only",
            "supervision": "functional association metadata only",
            "limitation": "not structural pocket labels",
        },
        "alphafold": {
            "role": "targeted PCNA predicted-structure context",
            "keep": "yes_context_only_if_needed",
            "supervision": "none",
            "limitation": "predicted structure is not pocket truth",
        },
        "pdbbind": {
            "role": "background affinity/source lead only",
            "keep": "exclude_from_primary_phase2_benchmark",
            "supervision": "affinity/protein-ligand complexes",
            "limitation": "not cryptic-pocket benchmark",
        },
    }
    rows = []
    for item in inventory.get("items", []):
        source = item["source_name"]
        role = role_map.get(source, {})
        rows.append(
            {
                "source_name": source,
                "role": role.get("role", item.get("intended_role")),
                "keep_recommendation": role.get("keep", "requires_review"),
                "supervision_meaning": role.get("supervision", "unknown"),
                "biological_limitations": role.get("limitation", "requires_schema_review"),
                "downloaded_files": item.get("downloaded_files", []),
                "linked_only_assets": item.get("linked_only_assets", []),
                "total_downloaded_bytes": item.get("total_downloaded_bytes", 0),
                "license_status": item.get("license_status"),
                "schema_status": item.get("schema_status"),
                "adoption_status": item.get("adoption_status"),
                "lifecycle_status": item.get("lifecycle_status"),
            }
        )
    if "pdbbind" not in {row["source_name"] for row in rows}:
        rows.append(
            {
                "source_name": "pdbbind",
                "role": role_map["pdbbind"]["role"],
                "keep_recommendation": role_map["pdbbind"]["keep"],
                "supervision_meaning": role_map["pdbbind"]["supervision"],
                "biological_limitations": role_map["pdbbind"]["limitation"],
                "downloaded_files": [],
                "linked_only_assets": [],
                "total_downloaded_bytes": 0,
                "license_status": "not_acquired_this_phase",
                "schema_status": "not_acquired_this_phase",
                "adoption_status": "not_adopted",
                "lifecycle_status": "excluded_from_primary_benchmark",
            }
        )
    return {
        "created_at": now(),
        "status": "auxiliary_sources_quarantined_not_adopted",
        "sources": rows,
    }


def common_provenance() -> list[str]:
    return [
        "",
        "## Provenance",
        "",
        f"- Date: {now()}",
        "- Command: `python scripts/phase2_remediation_packet.py`",
        "- Source paths: `reports/phase2/cryptobench_*`, `data/registries/cryptobench_*`, `data/registries/dataset_inventory.json`, `data/raw_intake/`",
        "- Governance paths: `docs/scientific_governance/04_DATASET_CONSTRAINTS.md`, `05_SPLIT_PROTOCOL.md`, `06_LABELING_RULES.md`, `07_PREPROCESSING_AND_GRAPH_RULES.md`, `12_PCNA_SPECIFIC_CHECKS.md`, `15_PROVENANCE_AND_REPRODUCIBILITY.md`, `19_STOP_CONDITIONS.md`, `21_READINESS_GATE.md`, `26_HUMAN_REVIEW_GATES.md`, `29_BENCHMARK_LIMITATIONS.md`",
        "- Confidence: high for local file-derived counts and registry generation; medium for recommended remediation status; low for unresolved homolog safety until clustering is run.",
        "- Evidence status: verified for local artifacts; inferred for planning recommendations; uncertain for final scientific usability.",
    ]


def main() -> int:
    for path in [DATASET_JSON, FOLDS_JSON, NONCRYPTIC_JSON, ZIP_PATH, SCHEMA_SUMMARY, FOLD_SUMMARY, STRUCTURE_INDEX, DATASET_INVENTORY]:
        if not path.is_file():
            print(f"Missing required input: {path}")
            return 1

    dataset = load_json(DATASET_JSON)
    folds = load_json(FOLDS_JSON)
    noncryptic = load_json(NONCRYPTIC_JSON)
    schema_summary = load_json(SCHEMA_SUMMARY)
    fold_summary = load_json(FOLD_SUMMARY)
    structure_index = load_json(STRUCTURE_INDEX)
    inventory = load_json(DATASET_INVENTORY)
    apo_to_fold = {apo_id: fold for fold, apo_ids in folds.items() for apo_id in apo_ids}
    cryptic_records = collect_records(dataset, "cryptic", apo_to_fold)
    noncryptic_records = collect_records(noncryptic, "noncryptic", apo_to_fold)
    all_records = cryptic_records + noncryptic_records

    pcna_screen = schema_summary["pcna_screen"]
    pcna_records = pcna_screen["pcna_records"]
    repeated_holos = repeated_holo_risks(cryptic_records)
    residue_failures = residue_mapping_failures(all_records)
    cleaned = candidate_cleaned_registry(cryptic_records, residue_failures, repeated_holos, pcna_records)

    homolog_risks = {
        "created_at": now(),
        "status": "potential_homolog_risks_not_resolved",
        "exact_uniprot_cross_fold_count": fold_summary["overlap"]["shared_uniprot_count"],
        "train_test_shared_uniprot_count": fold_summary["overlap"]["train_test_shared_uniprot_count"],
        "repeated_holo_pdb_across_folds_count": len(repeated_holos),
        "repeated_holo_pdb_across_folds": repeated_holos,
        "pcna_or_sliding_clamp_hits": pcna_screen,
        "required_next_methods": [
            "extract per-target-chain sequences preserving apo/holo grouping",
            "run approved sequence clustering tool and threshold",
            "review PCNA/sliding-clamp structural homologs",
            "group apo/holo/ligand variants before split assignment",
        ],
        "not_authorized": ["split_freeze", "label_freeze", "graph_generation", "training", "claims"],
    }
    aux_roles = inventory_roles(inventory)

    write_json(REGISTRIES["homolog_risks"], homolog_risks)
    write_json(REGISTRIES["residue_failures"], residue_failures)
    write_json(REGISTRIES["cleaned_registry"], cleaned)
    write_json(REGISTRIES["aux_roles"], aux_roles)

    write_report(
        REPORTS["adoption"],
        [
            "# CryptoBench Adoption Decision",
            "",
            "## Decision",
            "",
            "- Current decision: `not_adopted`.",
            "- Recommended path: `cryptic_only_benchmark_candidate_with_exclusions_and_split_redesign`.",
            "- Do not adopt the full CryptoBench bundle as-is.",
            "",
            "## Option Matrix",
            "",
            *render_table(
                ["Option", "Decision", "Reason"],
                [
                    ["Adopted with exclusions", "Possible later", "Requires PCNA isolation, repeated-holo grouping/exclusion, residue mapping remediation, homolog clustering, and human review."],
                    ["Cryptic-only adoption", "Preferred candidate path", "`dataset.json` has complete CIF coverage; noncryptic auxiliary records have missing structures and unresolved semantics."],
                    ["Benchmark-only", "Acceptable interim status", "Can remain an audited benchmark candidate while remediation is completed."],
                    ["Deferred/rejected", "Not required yet", "Current blockers are serious but appear remediable for cryptic-only use if human review approves."],
                ],
            ),
            "",
            "## Required Exclusions Or Holds Before Any Adoption",
            "",
            "- Exact PCNA record: apo `5e0v`, holo `3vkx`, UniProt `P12004`.",
            "- PCNA-like/sliding-clamp hits pending sequence and structural review: `2xur`, `3bep`, `3vkx`, `5e0v`.",
            "- Repeated-holo cross-fold systems until grouped or excluded.",
            "- Records with unresolved residue mapping failures until corrected or masked.",
            "- Noncryptic auxiliary records unless missing structures are acquired/subsetted and audited.",
            "",
            "## Adoption Preconditions",
            "",
            "- Human dataset adoption review.",
            "- PCNA isolation policy approval.",
            "- Sequence/homolog clustering and split redesign.",
            "- Label policy approval for partial/proxy supervision.",
            "- Residue mapping remediation or explicit masking policy.",
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["pcna_policy"],
        [
            "# PCNA Isolation Policy",
            "",
            "## Recommendation",
            "",
            "Use full PCNA isolation for Phase 2 model development. PCNA and PCNA-like sliding-clamp records must not appear in training, validation, threshold selection, feature-scaler fitting, architecture selection, or split tuning.",
            "",
            "## Policy",
            "",
            *render_table(
                ["Option", "Decision", "Reason"],
                [
                    ["Full exclusion from model development", "Required", "CryptoBench contains exact PCNA contamination and Phase 2 intends PCNA-facing interpretation later."],
                    ["External blind target", "Allowed later", "Only after model, split, labels, baselines, and report protocol are frozen."],
                    ["Held-out family", "Required if homologs/sliding clamps are found", "Sequence/structure relatives can leak PCNA-like features."],
                    ["Positive-control only", "Allowed with label", "PCNA records may be sanity checks, not independent validation."],
                    ["Inference-only target", "Allowed later", "No tuning or claims from inference-only PCNA targets without downstream gates."],
                ],
            ),
            "",
            "## Current PCNA Findings",
            "",
            *([f"- Exact PCNA record: apo `{r['apo_pdb_id']}` fold `{r['fold']}`, holo `{r['holo_pdb_id']}`, UniProt `{r['uniprot_id']}`, ligand `{r['ligand']}` `{r['ligand_index']}`." for r in pcna_records] or ["- No exact PCNA records found."]),
            *[f"- CIF text hit `{pdb_id}`: {', '.join(hits)}." for pdb_id, hits in pcna_screen["cif_text_hits"].items()],
            "",
            "## Required Before Split Freeze",
            "",
            "- Exclude or hold out exact PCNA apo/holo records.",
            "- Screen all CryptoBench structures for PCNA-like sliding clamps using sequence clustering and structural similarity review.",
            "- Record PCNA holdout/positive-control status in the split manifest.",
            "- Human review must approve the PCNA isolation decision.",
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["leakage"],
        [
            "# CryptoBench Leakage Remediation",
            "",
            "## Current Status",
            "",
            "- Official folds are not Phase 2-freezable.",
            "- Exact apo IDs do not overlap across folds.",
            f"- Exact UniProt IDs shared across folds: {fold_summary['overlap']['shared_uniprot_count']}.",
            f"- Holo PDB IDs repeated across folds: {len(repeated_holos)}.",
            "- Homolog leakage remains unresolved because no approved sequence clustering has been run.",
            "",
            "## Repeated Holo PDB IDs Across Folds",
            "",
            *render_table(
                ["Holo PDB", "Folds", "Apo IDs"],
                [
                    [
                        holo,
                        ", ".join(sorted({row["fold"] for row in rows})),
                        ", ".join(sorted({row["apo_pdb_id"] for row in rows})),
                    ]
                    for holo, rows in repeated_holos.items()
                ],
            ),
            "",
            "## Required Remediation",
            "",
            "- Build a system grouping key from UniProt ID, apo PDB, holo PDB, ligand, apo/holo pair, and sequence cluster.",
            "- Run sequence clustering before split assignment; a tool and threshold still require human approval.",
            "- Group all apo/holo records and ligand variants for a protein system into one split.",
            "- Isolate PCNA and PCNA-like sliding clamps from model development.",
            "- Treat official folds as source metadata only unless they pass the stricter Phase 2 leakage audit.",
            "",
            "## Structure Similarity Planning",
            "",
            "- Use structural review only after sequence grouping to catch remote homologs and sliding-clamp-like structures.",
            "- Candidate methods: Foldseek/DALI-style review if available, or documented manual review for PCNA/sliding-clamp hits.",
            "- No structure-similarity threshold is frozen in this packet.",
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["label_risks"],
        [
            "# Label Supervision Risks",
            "",
            "## Summary",
            "",
            "CryptoBench pocket selections can be considered candidate benchmark supervision only if Phase 2 explicitly treats them as partial, proxy pocket-region labels.",
            "",
            "## Risks",
            "",
            *render_table(
                ["Risk", "Status", "Consequence"],
                [
                    ["Unlisted residues are not true negatives", "Blocking for dense BCE without policy", "Metrics can reward false background assumptions."],
                    ["Pocket selections are proxy labels", "Known", "Cannot claim experimental cryptic truth for every residue."],
                    ["Noncryptic auxiliary structures missing", "Known", "Noncryptic records cannot be used as complete negative supervision."],
                    ["Residue-token mapping failures", f"{residue_failures['failure_count']} failures", "Label-node alignment can break."],
                    ["PCNA contamination", "Known", "PCNA final interpretation would be leaked if not isolated."],
                ],
            ),
            "",
            "## Defensible Direction",
            "",
            "- Use cryptic pocket selections as positive/partial-label supervision only after mapping failures are resolved or masked.",
            "- Treat unselected residues as unlabeled/background for training design until a human-approved negative policy exists.",
            "- Do not mix noncryptic auxiliary records into training before missing structures and semantics are resolved.",
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["label_policy"],
        [
            "# Proposed Label Policy",
            "",
            "## Proposed Status",
            "",
            "- Policy status: `draft_not_frozen`.",
            "- Label freeze remains blocked.",
            "",
            "## Proposed Supervision Contract",
            "",
            *render_table(
                ["Field", "Proposed policy"],
                [
                    ["Positive label source", "CryptoBench `dataset.json` `apo_pocket_selection` mapped to resolved apo residues."],
                    ["Label type", "Proxy benchmark cryptic pocket-region positive."],
                    ["Negative label source", "None frozen."],
                    ["Unlisted residues", "Background/unlabeled, not true negatives by default."],
                    ["Ambiguous residues", "Mask until residue mapping and missing-residue policy pass."],
                    ["Noncryptic pockets", "Audit/reference only until missing structures and semantics are resolved."],
                    ["PCNA labels", "Holdout or positive-control only; not model development."],
                    ["Dense residue classification", "Not scientifically justified until partial-label strategy or approved background-negative policy is reviewed."],
                ],
            ),
            "",
            "## Required Before Label Freeze",
            "",
            "- Resolve or mask residue mapping failures.",
            "- Define whether training uses positive-unlabeled, masked BCE, ranking/top-k, or another documented objective.",
            "- Record ligand/contact semantics and excluded ligand classes.",
            "- Human label review must approve the policy.",
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["residue_failures"],
        [
            "# Residue Mapping Failure Analysis",
            "",
            "## Summary",
            "",
            f"- Selection tokens checked against present CIF atom-site residue IDs: {residue_failures['checked_selection_tokens_with_present_cifs']}.",
            f"- Mapping failures: {residue_failures['failure_count']}.",
            f"- Selection tokens skipped because referenced CIFs are missing: {residue_failures['missing_cif_selection_token_count']}.",
            "",
            "## Failure Reasons",
            "",
            *render_table(
                ["Reason", "Count"],
                [[reason, count] for reason, count in sorted(residue_failures["failure_reason_counts"].items())],
            ),
            "",
            "## Interpretation",
            "",
            "- Failures include auth/label numbering mismatches, residues absent from resolved atom-site records, and missing auxiliary CIF references.",
            "- These failures block graph generation until a residue-node and masking policy is approved.",
            f"- Full machine-readable failure table: `{rel(REGISTRIES['residue_failures'])}`.",
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["split_strategy"],
        [
            "# Proposed Phase 2 Split Strategy",
            "",
            "## Status",
            "",
            "- Strategy status: `draft_not_frozen`.",
            "- Split freeze remains blocked.",
            "",
            "## Candidate Split Design",
            "",
            "1. Start from CryptoBench cryptic `dataset.json` only.",
            "2. Remove or isolate exact PCNA and PCNA-like sliding-clamp records.",
            "3. Build system groups using UniProt, apo/holo pair, ligand variants, repeated holo structures, sequence cluster, and structural review flags.",
            "4. Assign train/validation/test by group, never by residue or graph.",
            "5. Keep PCNA/external targets out of train/validation/test model development if they may support later PCNA interpretation.",
            "",
            "## Candidate Split Families",
            "",
            *render_table(
                ["Candidate", "Purpose", "Status"],
                [
                    ["Sequence-cluster split", "Controls close homolog leakage", "planned; tool/threshold not frozen"],
                    ["Homolog-aware split", "Groups families beyond exact UniProt", "planned; requires clustering"],
                    ["Family-isolation split", "Stress-tests generalization", "optional after clusters exist"],
                    ["Apo/holo grouped split", "Prevents paired-structure leakage", "required"],
                    ["PCNA holdout split", "Protects PCNA interpretation", "required if PCNA remains in any source set"],
                ],
            ),
            "",
            "## Freeze Preconditions",
            "",
            "- Sequence clustering completed and registered.",
            "- Repeated holo PDB IDs resolved by grouping/exclusion.",
            "- PCNA isolation approved.",
            "- Label policy approved.",
            "- Human split review recorded.",
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["cleaned_registry"],
        [
            "# CryptoBench Candidate Cleaned Registry",
            "",
            "## Status",
            "",
            "- Registry status: `candidate_not_adopted_not_frozen`.",
            "- This is a planning registry, not a frozen dataset registry.",
            "",
            "## Recommendation",
            "",
            "- Preferred path: cryptic-only benchmark candidate with exclusions, PCNA isolation, residue-failure remediation, and new homolog-aware split.",
            "- Do not use noncryptic auxiliary records for training until missing structures are resolved.",
            "",
            "## Counts",
            "",
            f"- Total cryptic records: {cleaned['total_cryptic_records']}.",
            f"- Excluded or review-required records: {cleaned['excluded_or_review_required_record_count']}.",
            f"- PCNA holdout records: {cleaned['holdout_record_count']}.",
            f"- Full machine-readable registry: `{rel(REGISTRIES['cleaned_registry'])}`.",
            *common_provenance(),
        ],
    )

    aux_rows = aux_roles["sources"]
    write_report(
        REPORTS["role_table"],
        [
            "# Benchmark Role Classification Table",
            "",
            *render_table(
                ["Source", "Role", "Keep recommendation", "Supervision meaning", "Limitation"],
                [
                    [
                        row["source_name"],
                        row["role"],
                        row["keep_recommendation"],
                        row["supervision_meaning"],
                        row["biological_limitations"],
                    ]
                    for row in aux_rows
                ],
            ),
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["aux_audit"],
        [
            "# Auxiliary Dataset Audit",
            "",
            "## Status",
            "",
            "- Auxiliary assets remain `raw_unverified` and `not_adopted`.",
            "- None are accepted cryptic-pocket truth.",
            "",
            "## Findings",
            "",
            "- BioLiP/Q-BioLiP: useful ligand-contact context only after terms/schema review; not cryptic-pocket truth.",
            "- scPDB: possible binding-pocket proxy source, but terms/bulk/schema unresolved.",
            "- ASD: allosteric context/reference only unless entry-level labels are separately audited.",
            "- PocketMiner: useful baseline/method reference; overlap with CryptoBench must be audited.",
            "- fpocket/P2Rank: baseline tool metadata acquired; installation/output schema still pending.",
            "- BioGRID/STRING: PCNA context only, not structural pocket labels.",
            "- AlphaFold P12004: targeted predicted-structure metadata only, not supervision.",
            "- PDBbind: excluded from primary benchmark role; retain only as background/source lead if needed.",
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["acquisition"],
        [
            "# Auxiliary Acquisition Status Summary",
            "",
            *render_table(
                ["Source", "Downloaded files", "Linked assets", "Bytes", "License", "Schema", "Lifecycle"],
                [
                    [
                        row["source_name"],
                        len(row["downloaded_files"]),
                        len(row["linked_only_assets"]),
                        row["total_downloaded_bytes"],
                        row["license_status"],
                        row["schema_status"],
                        row["lifecycle_status"],
                    ]
                    for row in aux_rows
                ],
            ),
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["footprint"],
        [
            "# Dataset Footprint Summary",
            "",
            *render_table(
                ["Source", "Downloaded bytes", "Downloaded file count", "Linked-only count", "Adoption status"],
                [
                    [
                        row["source_name"],
                        row["total_downloaded_bytes"],
                        len(row["downloaded_files"]),
                        len(row["linked_only_assets"]),
                        row["adoption_status"],
                    ]
                    for row in aux_rows
                ],
            ),
            "",
            "All files remain quarantined. The 20 GB total budget remains active; no new bulk file over 500 MB was downloaded in this remediation packet.",
            *common_provenance(),
        ],
    )

    write_report(
        REPORTS["handoff"],
        [
            "# Phase 2 Claude Code Handoff",
            "",
            "## Current Status",
            "",
            "- Everything remains `raw_unverified`, `not_adopted`, and `not_ready_for_training`.",
            "- Do not train, generate graphs, run MD, freeze labels, freeze splits, or make scientific claims.",
            "",
            "## Track A Outputs",
            "",
            *[f"- `{rel(path)}`" for path in [REPORTS["adoption"], REPORTS["pcna_policy"], REPORTS["leakage"], REPORTS["label_risks"], REPORTS["label_policy"], REPORTS["residue_failures"], REPORTS["split_strategy"], REPORTS["cleaned_registry"], REGISTRIES["homolog_risks"], REGISTRIES["residue_failures"], REGISTRIES["cleaned_registry"]]],
            "",
            "## Track B Outputs",
            "",
            *[f"- `{rel(path)}`" for path in [REPORTS["aux_audit"], REPORTS["role_table"], REPORTS["acquisition"], REPORTS["footprint"], REGISTRIES["aux_roles"], DATASET_INVENTORY]],
            "",
            "## Highest-Priority Next Work",
            "",
            "1. Human review: decide CryptoBench cryptic-only adoption with exclusions versus benchmark-only/defer.",
            "2. Choose sequence clustering tool/threshold and run clustering before split freeze.",
            "3. Resolve or mask residue mapping failures.",
            "4. Approve a partial-label/positive-unlabeled supervision policy.",
            "5. Draft a split manifest only after PCNA isolation and grouping rules are accepted.",
            *common_provenance(),
        ],
    )

    print("Wrote Phase 2 remediation and auxiliary handoff packet.")
    for path in [*REPORTS.values(), *REGISTRIES.values()]:
        print(rel(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
