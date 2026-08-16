"""Deterministic verification and extraction for the approved CryptoBench CIF zip."""

from __future__ import annotations

import shutil
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from phase3_data import constants
from phase3_data.errors import Phase3DataError
from phase3_data.hashing import sha256_file
from phase3_data.models import Phase3Paths
from phase3_data.provenance import process_context


def count_cif_files(cif_dir: Path) -> int:
    if not cif_dir.is_dir():
        return 0
    return sum(1 for path in cif_dir.glob("*.cif") if path.is_file())


def inspect_cif_inputs(paths: Phase3Paths) -> dict[str, Any]:
    cif_dir = paths.cif_dir_path
    cif_zip = paths.cif_zip_path
    extracted_count = count_cif_files(cif_dir)
    zip_exists = cif_zip.is_file()
    status = "READY" if extracted_count == constants.EXPECTED_CIF_FILE_COUNT else "EXTRACTION_REQUIRED"
    if not zip_exists and status != "READY":
        status = "MISSING_CIF_DIR_AND_ZIP"
    return {
        "status": status,
        "cif_dir": str(cif_dir),
        "cif_dir_exists": cif_dir.is_dir(),
        "extracted_cif_count": extracted_count,
        "expected_cif_count": constants.EXPECTED_CIF_FILE_COUNT,
        "cif_zip": str(cif_zip),
        "cif_zip_exists": zip_exists,
        "remediation": (
            "Run `python -m phase3_data.cli verify-or-extract-cifs` with PYTHONPATH=src."
            if status == "EXTRACTION_REQUIRED"
            else None
        ),
    }


def verify_cif_zip(zip_path: Path) -> dict[str, Any]:
    if not zip_path.is_file():
        raise Phase3DataError(f"Approved CryptoBench CIF zip is missing: {zip_path}")
    actual_hash = sha256_file(zip_path)
    if actual_hash != constants.EXPECTED_CIF_ZIP_SHA256:
        raise Phase3DataError(
            f"CryptoBench CIF zip hash mismatch: expected {constants.EXPECTED_CIF_ZIP_SHA256}, got {actual_hash}"
        )
    try:
        with zipfile.ZipFile(zip_path) as archive:
            file_infos = [info for info in archive.infolist() if not info.is_dir()]
    except zipfile.BadZipFile as exc:
        raise Phase3DataError(f"CryptoBench CIF zip is not readable: {zip_path}") from exc
    if len(file_infos) != constants.EXPECTED_CIF_FILE_COUNT:
        raise Phase3DataError(
            f"CryptoBench CIF zip file-count mismatch: expected {constants.EXPECTED_CIF_FILE_COUNT}, "
            f"got {len(file_infos)}."
        )
    return {
        "zip_path": str(zip_path),
        "zip_hash_sha256": actual_hash,
        "zip_file_count": len(file_infos),
        "first_member": file_infos[0].filename if file_infos else None,
        "last_member": file_infos[-1].filename if file_infos else None,
    }


def _safe_member_target(info: zipfile.ZipInfo, target_dir: Path) -> Path | None:
    name = PurePosixPath(info.filename)
    if info.is_dir():
        return None
    if name.is_absolute() or ".." in name.parts:
        raise Phase3DataError(f"Unsafe zip member path rejected: {info.filename}")
    if not name.parts or name.parts[0] != "cif-files":
        raise Phase3DataError(f"Unexpected zip member outside cif-files/: {info.filename}")
    rel_parts = name.parts[1:]
    if not rel_parts:
        return None
    target = (target_dir / Path(*rel_parts)).resolve()
    root = target_dir.resolve()
    if target != root and root not in target.parents:
        raise Phase3DataError(f"Unsafe extraction target rejected: {target}")
    return target


def extract_cif_zip(paths: Phase3Paths, command: str) -> dict[str, Any]:
    zip_info = verify_cif_zip(paths.cif_zip_path)
    target_dir = paths.cif_dir_path
    target_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[str] = []
    with zipfile.ZipFile(paths.cif_zip_path) as archive:
        for info in archive.infolist():
            target = _safe_member_target(info, target_dir)
            if target is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            extracted.append(str(target))
    extracted_count = count_cif_files(target_dir)
    if extracted_count != constants.EXPECTED_CIF_FILE_COUNT:
        raise Phase3DataError(
            f"Extraction finished with {extracted_count} CIF files; expected {constants.EXPECTED_CIF_FILE_COUNT}."
        )
    sample_hashes = {
        path.name: sha256_file(path)
        for path in sorted(target_dir.glob("*.cif"))[:10]
    }
    manifest = {
        "artifact_type": "phase3_cif_extraction_manifest",
        "status": "PASS",
        "action": "extracted",
        **process_context(paths.root, command),
        **zip_info,
        "target_dir": str(target_dir),
        "extracted_file_count": extracted_count,
        "sample_extracted_hashes": sample_hashes,
        "governance": [
            "docs/scientific_governance/07_PREPROCESSING_AND_GRAPH_RULES.md",
            "docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md",
            "docs/scientific_governance/26_HUMAN_REVIEW_GATES.md",
        ],
        "notes": "Extraction only. No graph generation, training artifacts, or model gradients were produced.",
    }
    return manifest


def verify_or_extract_cifs(paths: Phase3Paths, command: str) -> dict[str, Any]:
    state = inspect_cif_inputs(paths)
    if state["status"] == "READY":
        sample_hashes = {
            path.name: sha256_file(path)
            for path in sorted(paths.cif_dir_path.glob("*.cif"))[:10]
        }
        return {
            "artifact_type": "phase3_cif_extraction_manifest",
            "status": "PASS",
            "action": "verified_existing",
            **process_context(paths.root, command),
            "target_dir": str(paths.cif_dir_path),
            "extracted_file_count": state["extracted_cif_count"],
            "sample_extracted_hashes": sample_hashes,
            "zip_path": str(paths.cif_zip_path),
            "zip_hash_sha256": sha256_file(paths.cif_zip_path) if paths.cif_zip_path.is_file() else None,
            "notes": "Existing extracted CIF directory verified by count. No graph generation or training occurred.",
        }
    if state["status"] == "MISSING_CIF_DIR_AND_ZIP":
        raise Phase3DataError(
            f"CIF directory is absent ({paths.cif_dir_path}) and approved zip is missing ({paths.cif_zip_path})."
        )
    return extract_cif_zip(paths, command)

