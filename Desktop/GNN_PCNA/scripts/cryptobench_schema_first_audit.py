#!/usr/bin/env python3
"""Schema-first audit for quarantined CryptoBench raw intake.

This script inspects JSON structure and ZIP inventory only. It does not adopt
data, generate graphs, train models, run MD, or freeze splits/labels.
"""

from __future__ import annotations

import json
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw_intake" / "cryptobench"
REPORT = ROOT / "reports" / "phase2" / "cryptobench_schema_first_audit.md"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def describe_json(path: Path) -> dict[str, Any]:
    data = load_json(path)
    result: dict[str, Any] = {
        "path": str(path.relative_to(ROOT)),
        "size_bytes": path.stat().st_size,
        "top_level_type": type(data).__name__,
        "top_level_len": len(data) if hasattr(data, "__len__") else None,
        "top_level_keys": list(data.keys())[:30] if isinstance(data, dict) else None,
        "sample": None,
    }
    if isinstance(data, list) and data:
        first = data[0]
        result["sample_type"] = type(first).__name__
        result["sample_keys"] = list(first.keys())[:40] if isinstance(first, dict) else None
    elif isinstance(data, dict):
        sample_items = []
        for key, value in list(data.items())[:5]:
            item = {
                "key": key,
                "value_type": type(value).__name__,
                "value_len": len(value) if hasattr(value, "__len__") else None,
            }
            if isinstance(value, dict):
                item["value_keys"] = list(value.keys())[:20]
            elif isinstance(value, list) and value:
                item["first_item_type"] = type(value[0]).__name__
                if isinstance(value[0], dict):
                    item["first_item_keys"] = list(value[0].keys())[:20]
            sample_items.append(item)
        result["sample"] = sample_items
    return result


def zip_inventory(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path, "r") as archive:
        infos = archive.infolist()
    suffix_counts = Counter(Path(info.filename).suffix.lower() or "<none>" for info in infos if not info.is_dir())
    top_dirs = Counter((Path(info.filename).parts[0] if Path(info.filename).parts else "<root>") for info in infos)
    return {
        "path": str(path.relative_to(ROOT)),
        "size_bytes": path.stat().st_size,
        "can_open": True,
        "file_count": sum(1 for info in infos if not info.is_dir()),
        "dir_count": sum(1 for info in infos if info.is_dir()),
        "total_uncompressed_bytes": sum(info.file_size for info in infos),
        "suffix_counts": dict(sorted(suffix_counts.items())),
        "top_dirs": dict(top_dirs.most_common(20)),
        "first_entries": [info.filename for info in infos[:40]],
    }


def bullet_json_description(desc: dict[str, Any]) -> list[str]:
    lines = [
        f"### `{desc['path']}`",
        "",
        f"- Size bytes: {desc['size_bytes']}",
        f"- Top-level type: `{desc['top_level_type']}`",
        f"- Top-level length: `{desc['top_level_len']}`",
    ]
    if desc.get("top_level_keys"):
        lines.append("- Top-level keys: " + ", ".join(f"`{key}`" for key in desc["top_level_keys"]))
    if desc.get("sample_keys"):
        lines.append("- First list item keys: " + ", ".join(f"`{key}`" for key in desc["sample_keys"]))
    if desc.get("sample"):
        lines.append("- Sample nested structure:")
        for item in desc["sample"]:
            line = f"  - `{item['key']}`: {item['value_type']}"
            if item.get("value_len") is not None:
                line += f" len={item['value_len']}"
            if item.get("value_keys"):
                line += " keys=" + ", ".join(f"`{key}`" for key in item["value_keys"])
            if item.get("first_item_keys"):
                line += " first_item_keys=" + ", ".join(f"`{key}`" for key in item["first_item_keys"])
            lines.append(line)
    lines.append("")
    return lines


def main() -> int:
    dataset_json = RAW / "metadata_files" / "66c328c87352852f68dbeac4_dataset.json"
    folds_json = RAW / "metadata_files" / "66c328d97352852f68dbead5_folds.json"
    fold_files = sorted((RAW / "labels_or_splits").glob("*.json"))
    noncryptic = [path for path in fold_files if "noncryptic" in path.name.lower()]
    train_test = [path for path in fold_files if "train" in path.name.lower() or "test" in path.name.lower()]
    zip_path = RAW / "files" / "672a0171eae0bff252ba9ea3_cif-files.zip"

    missing = [path for path in [dataset_json, folds_json, zip_path] if not path.is_file()]
    if missing:
        print("Missing required CryptoBench audit inputs:")
        for path in missing:
            print(f"- {path}")
        return 1

    descriptions = [describe_json(dataset_json), describe_json(folds_json)]
    descriptions.extend(describe_json(path) for path in train_test)
    descriptions.extend(describe_json(path) for path in noncryptic if path not in train_test)
    zip_desc = zip_inventory(zip_path)

    lines = [
        "# CryptoBench Schema-First Audit",
        "",
        "## Conservative Status",
        "",
        "- Final status: `CRYPTOBENCH_READY_FOR_SCHEMA_AUDIT`",
        "- Adoption status: `not_adopted`",
        "- Quarantine status: `raw_unverified`",
        "- Training, graph generation, split freeze, label freeze, evaluation, MD, and claims remain blocked.",
        "",
        "## Scope",
        "",
        "This audit inspects the top-level structure of acquired CryptoBench JSON files and the inventory of `cif-files.zip` only. It does not extract the archive into canonical data folders and does not validate labels, splits, leakage, PCNA contamination, or biological meaning.",
        "",
        "## JSON Schema First Pass",
        "",
    ]
    for desc in descriptions:
        lines.extend(bullet_json_description(desc))

    lines.extend(
        [
            "## ZIP Inventory Only",
            "",
            f"- Path: `{zip_desc['path']}`",
            f"- Size bytes: {zip_desc['size_bytes']}",
            f"- Can open safely with Python zipfile: `{zip_desc['can_open']}`",
            f"- File count: {zip_desc['file_count']}",
            f"- Directory count: {zip_desc['dir_count']}",
            f"- Total uncompressed bytes: {zip_desc['total_uncompressed_bytes']}",
            "- Suffix counts: "
            + ", ".join(f"`{suffix}`={count}" for suffix, count in zip_desc["suffix_counts"].items()),
            "- Top directories: "
            + ", ".join(f"`{name}`={count}" for name, count in zip_desc["top_dirs"].items()),
            "",
            "### First ZIP Entries",
            "",
        ]
    )
    lines.extend(f"- `{entry}`" for entry in zip_desc["first_entries"])
    lines.extend(
        [
            "",
            "## Interpretation Limits",
            "",
            "- JSON schema visibility is partial until a formal schema audit maps records to structures, labels, residues, chains, apo/holo pairs, and splits.",
            "- ZIP inventory visibility confirms the archive can be listed, not that its structures are scientifically usable.",
            "- PCNA/homolog contamination screening has not been completed.",
            "- Leakage audits and human dataset/label/split review are still required.",
            "",
            "## Provenance",
            "",
            f"- Date: {now()}",
            "- Script/command used: `python scripts/cryptobench_schema_first_audit.py`",
            "- Source paths inspected: `data/raw_intake/cryptobench/metadata_files/`, `data/raw_intake/cryptobench/labels_or_splits/`, `data/raw_intake/cryptobench/files/672a0171eae0bff252ba9ea3_cif-files.zip`",
            "- Confidence level: high for local file inventory and JSON/ZIP readability; uncertain for scientific usability.",
            "- Evidence status: verified for local file structure; inferred for schema meaning; uncertain for labels/leakage/biological use.",
            "- Unresolved questions: label semantics, residue mapping, chain mapping, apo/holo grouping, PCNA/homolog contamination, leakage, and human review.",
            "",
        ]
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("Final status: CRYPTOBENCH_READY_FOR_SCHEMA_AUDIT")
    print("Training readiness: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
