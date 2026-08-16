"""Per-structure label loading with positive-unlabeled semantics."""

from __future__ import annotations

import re
from pathlib import Path

from phase3_data import constants
from phase3_data.errors import Phase3DataError
from phase3_data.io import read_json
from phase3_data.models import LabelRecord


_RESIDUE_TOKEN_RE = re.compile(r"^(?P<number>-?\d+)(?P<icode>[A-Za-z]?)$")


def parse_target_chains(chain_field: str) -> tuple[str, ...]:
    if not chain_field:
        raise Phase3DataError("Label file is missing target chain field.")
    chains = tuple(part.strip() for part in chain_field.replace(",", "-").split("-") if part.strip())
    if not chains:
        raise Phase3DataError(f"Unable to parse target chain field: {chain_field!r}")
    return chains


def parse_label_key(label_key: str, label_value: int) -> LabelRecord:
    if "_" not in label_key:
        raise Phase3DataError(f"Invalid label key {label_key!r}; expected '<chain>_<residue>'.")
    chain_id, residue_token = label_key.split("_", 1)
    match = _RESIDUE_TOKEN_RE.match(residue_token)
    residue_number = match.group("number") if match else residue_token
    insertion_code = match.group("icode") or None if match else None
    if label_value not in constants.LABEL_VALUES:
        raise Phase3DataError(f"Invalid label value {label_value!r} for {label_key}.")
    if label_value == 1:
        role = "positive"
        loss_mask = True
    elif label_value == -1:
        role = "masked_from_loss"
        loss_mask = False
    else:
        role = "background_unlabeled"
        loss_mask = True
    return LabelRecord(
        label_key=label_key,
        chain_id=chain_id,
        residue_token=residue_token,
        residue_number=residue_number,
        insertion_code=insertion_code,
        label=label_value,
        loss_mask=loss_mask,
        supervision_role=role,
    )


def background_record(label_key: str, chain_id: str, residue_number: str, insertion_code: str | None) -> LabelRecord:
    token = f"{residue_number}{insertion_code or ''}"
    return LabelRecord(
        label_key=label_key,
        chain_id=chain_id,
        residue_token=token,
        residue_number=residue_number,
        insertion_code=insertion_code,
        label=0,
        loss_mask=True,
        supervision_role="background_unlabeled",
    )


def load_structure_label_file(path: Path) -> tuple[dict, dict[str, LabelRecord]]:
    data = read_json(path)
    if data.get("governance") != "docs/scientific_governance/06_LABELING_RULES.md":
        raise Phase3DataError(f"Label file {path} does not reference labeling governance.")
    labels = data.get("labels")
    if not isinstance(labels, dict):
        raise Phase3DataError(f"Label file {path} is missing labels object.")
    records = {key: parse_label_key(key, int(value)) for key, value in labels.items()}
    positive_count = sum(1 for record in records.values() if record.label == 1)
    masked_count = sum(1 for record in records.values() if record.label == -1)
    if positive_count != data.get("positive_count"):
        raise Phase3DataError(f"Positive count mismatch in {path}.")
    if masked_count != data.get("masked_count"):
        raise Phase3DataError(f"Masked count mismatch in {path}.")
    return data, records

