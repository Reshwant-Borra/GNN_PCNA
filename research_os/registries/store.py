"""RegistryStore: atomic JSON storage for ResearchOS registries.

Design rules:

- Every entry gets a stable string ID (`ART-0001`, `CLAIM-0001`, ...).
- Writes are atomic: temp file -> fsync -> os.replace -> target.
- Entries are never destructively deleted; status fields drive lifecycle.
- Validation runs before writing; bad entries raise RegistryValidationError.
- The store is the single source of truth — agents propose updates via the
  orchestrator and never write their own JSON.
"""
from __future__ import annotations

import json
import os
import tempfile
import threading
import shutil
from dataclasses import fields
from dataclasses import is_dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from research_os.schemas.registries import (
    ArtifactEntry,
    ClaimEntry,
    DecisionEntry,
    EnvironmentEntry,
    ExperimentEntry,
    IssueEntry,
    SourceEntry,
)
from research_os.schemas.vocab import ARTIFACT_TYPES, CLAIM_STRENGTHS


REGISTRY_NAMES: Tuple[str, ...] = (
    "artifact_registry",
    "claim_registry",
    "experiment_registry",
    "issue_registry",
    "source_registry",
    "environment_registry",
    "decision_registry",
)

REGISTRY_SCHEMA_VERSION = "2.0"

REGISTRY_ID_PREFIXES: Dict[str, str] = {
    "artifact_registry": "ART",
    "claim_registry": "CLAIM",
    "experiment_registry": "EXP",
    "issue_registry": "ISSUE",
    "source_registry": "SRC",
    "environment_registry": "ENV",
    "decision_registry": "DEC",
}

_REGISTRY_DATACLASSES: Dict[str, type] = {
    "artifact_registry": ArtifactEntry,
    "claim_registry": ClaimEntry,
    "experiment_registry": ExperimentEntry,
    "issue_registry": IssueEntry,
    "source_registry": SourceEntry,
    "environment_registry": EnvironmentEntry,
    "decision_registry": DecisionEntry,
}

_REGISTRY_ID_FIELDS: Dict[str, str] = {
    "artifact_registry": "artifact_id",
    "claim_registry": "claim_id",
    "experiment_registry": "experiment_id",
    "issue_registry": "issue_id",
    "source_registry": "source_id",
    "environment_registry": "environment_id",
    "decision_registry": "decision_id",
}

_LEGACY_ENTRY_KEYS: Dict[str, str] = {
    "artifact_registry": "artifacts",
    "claim_registry": "claims",
    "experiment_registry": "experiments",
    "issue_registry": "issues",
    "source_registry": "sources",
    "environment_registry": "environments",
    "decision_registry": "decisions",
}

_DATACLASS_FIELD_NAMES: Dict[str, set[str]] = {
    name: {f.name for f in fields(cls)}
    for name, cls in _REGISTRY_DATACLASSES.items()
}


class RegistryValidationError(ValueError):
    """Raised when a registry entry fails closed-vocabulary or shape validation."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_path(name: str) -> str:
    if name not in REGISTRY_NAMES:
        raise ValueError(
            f"Unknown registry {name!r}. Allowed: {REGISTRY_NAMES}"
        )
    return name


def _to_dict(entry: Any) -> Dict[str, Any]:
    if isinstance(entry, dict):
        return entry
    if is_dataclass(entry):
        return asdict(entry)
    raise TypeError(f"Cannot serialize entry of type {type(entry).__name__}")


def _coerce_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _filter_for_dataclass(name: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in raw.items() if k in _DATACLASS_FIELD_NAMES[name]}


class RegistryStore:
    """File-backed registry with atomic writes."""

    def __init__(self, base_dir: Path | str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    # ----- paths -----

    def path_for(self, name: str) -> Path:
        _ensure_path(name)
        return self.base_dir / f"{name}.json"

    # ----- io -----

    def load(self, name: str) -> Dict[str, Any]:
        """Load a registry file. Returns the default empty shape if missing."""
        path = self.path_for(name)
        if not path.exists():
            return self._empty_registry(name)
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise RegistryValidationError(
                f"{path} contains invalid JSON: {e}"
            ) from e
        data, migrated = self._migrate_if_needed(name, data, path)
        if migrated:
            self._atomic_write(path, data)
        if not isinstance(data, dict) or "entries" not in data:
            raise RegistryValidationError(
                f"{path} is malformed; expected an object with an 'entries' list"
            )
        if not isinstance(data["entries"], list):
            raise RegistryValidationError(
                f"{path} is malformed; expected 'entries' to be a list"
            )
        return data

    def _empty_registry(self, name: str) -> Dict[str, Any]:
        now = _utc_now_iso()
        return {
            "registry": name,
            "id_prefix": REGISTRY_ID_PREFIXES[name],
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "created_at": now,
            "updated_at": now,
            "entries": [],
        }

    def _backup_before_migration(self, path: Path) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_path = path.with_name(f"{path.name}.bak-{timestamp}")
        suffix = 1
        while backup_path.exists():
            backup_path = path.with_name(f"{path.name}.bak-{timestamp}-{suffix}")
            suffix += 1
        shutil.copy2(path, backup_path)
        return backup_path

    def _migrate_if_needed(
        self, name: str, data: Any, path: Path
    ) -> Tuple[Dict[str, Any], bool]:
        if not isinstance(data, dict):
            raise RegistryValidationError(
                f"{path} is malformed; expected a JSON object"
            )

        legacy_key = _LEGACY_ENTRY_KEYS.get(name)
        has_legacy_entries = bool(
            legacy_key and legacy_key in data and "entries" not in data
        )
        needs_version = data.get("schema_version") != REGISTRY_SCHEMA_VERSION
        if not has_legacy_entries and "entries" in data and not needs_version:
            return data, False

        if "entries" not in data and not has_legacy_entries:
            raise RegistryValidationError(
                f"{path} is malformed; expected an object with an 'entries' list"
            )

        if path.exists():
            self._backup_before_migration(path)

        now = _utc_now_iso()
        source_entries = data.get(legacy_key) if has_legacy_entries else data.get("entries", [])
        if not isinstance(source_entries, list):
            raise RegistryValidationError(
                f"{path} is malformed; expected '{legacy_key or 'entries'}' to be a list"
            )

        migrated = dict(data)
        if legacy_key:
            migrated.pop(legacy_key, None)
        migrated.setdefault("registry", name)
        migrated["id_prefix"] = migrated.get("id_prefix") or migrated.get("_id_prefix") or REGISTRY_ID_PREFIXES[name]
        migrated.setdefault("created_at", data.get("created_at") or now)
        migrated["updated_at"] = now
        migrated["schema_version"] = REGISTRY_SCHEMA_VERSION
        if has_legacy_entries:
            migrated["migrated_at"] = now
            migrated["migrated_from"] = {
                "entry_key": legacy_key,
                "schema_version": data.get("schema_version") or data.get("_schema_version", ""),
            }
            migrated["_legacy_metadata"] = {
                k: v for k, v in data.items() if k != legacy_key
            }
        migrated["entries"] = [
            self._migrate_entry(name, raw) for raw in source_entries
        ]
        return migrated, True

    def _migrate_entry(self, name: str, raw: Any) -> Any:
        if not isinstance(raw, dict):
            return raw
        if name == "claim_registry":
            return self._migrate_claim_entry(raw)
        if name == "artifact_registry":
            return self._migrate_artifact_entry(raw)
        if name == "experiment_registry":
            return self._migrate_experiment_entry(raw)
        if name == "issue_registry":
            return self._migrate_issue_entry(raw)
        if name == "source_registry":
            return self._migrate_source_entry(raw)
        return self._migrate_common_entry(name, raw)

    def _migrate_common_entry(self, name: str, raw: Dict[str, Any]) -> Dict[str, Any]:
        entry = dict(raw)
        id_field = _REGISTRY_ID_FIELDS[name]
        if id_field not in entry and "id" in raw:
            entry[id_field] = raw["id"]
        if "created_at" not in entry and "created" in raw:
            entry["created_at"] = raw["created"]
        if "updated_at" not in entry and "updated" in raw:
            entry["updated_at"] = raw["updated"]
        entry.setdefault("_legacy", dict(raw))
        return entry

    def _migrate_claim_entry(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entry = self._migrate_common_entry("claim_registry", raw)
        if "claim_id" not in entry and "id" in raw:
            entry["claim_id"] = raw["id"]
        if "claim_text" not in entry and "text" in raw:
            entry["claim_text"] = raw["text"]
        if "created_at" not in entry and "created" in raw:
            entry["created_at"] = raw["created"]
        if "updated_at" not in entry and "updated" in raw:
            entry["updated_at"] = raw["updated"]
        if "claim_strength" not in entry:
            entry["claim_strength"] = raw.get("status") or "hypothesis_generating"
        if entry.get("claim_strength") not in CLAIM_STRENGTHS:
            entry["legacy_claim_strength"] = entry.get("claim_strength")
            entry["claim_strength"] = "hypothesis_generating"
        if entry.get("status") not in CLAIM_STRENGTHS:
            entry["legacy_status"] = entry.get("status")
            entry["status"] = entry["claim_strength"]
        if "allowed_wording" in entry:
            entry["allowed_wording"] = _coerce_list(entry["allowed_wording"])
        if "disallowed_wording" in entry:
            entry["disallowed_wording"] = _coerce_list(entry["disallowed_wording"])
        if "human_approval" not in entry:
            required = bool(raw.get("requires_human_approval", False))
            approved = bool(raw.get("human_approved", False))
            entry["human_approval"] = {
                "required": required,
                "decision_id": "",
                "approval_status": "approved" if approved else ("pending" if required else "not_required"),
            }
        return entry

    def _migrate_artifact_entry(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entry = self._migrate_common_entry("artifact_registry", raw)
        if "artifact_id" not in entry and "id" in raw:
            entry["artifact_id"] = raw["id"]
        if "artifact_type" not in entry and "type" in raw:
            entry["artifact_type"] = raw["type"]
        if "artifact_type" not in entry:
            entry["artifact_type"] = "other"
        elif entry["artifact_type"] not in ARTIFACT_TYPES:
            entry["legacy_artifact_type"] = entry["artifact_type"]
            entry["artifact_type"] = "other"
        if "created_by_agent" not in entry and "created_by" in raw:
            entry["created_by_agent"] = raw["created_by"]
        return entry

    def _migrate_experiment_entry(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entry = self._migrate_common_entry("experiment_registry", raw)
        if "title" not in entry and "name" in raw:
            entry["title"] = raw["name"]
        if "hypothesis_tested" not in entry and "hypothesis" in raw:
            entry["hypothesis_tested"] = raw["hypothesis"]
        if "script_or_workflow" not in entry and "script" in raw:
            entry["script_or_workflow"] = raw["script"]
        if "input_artifacts" not in entry and "inputs" in raw:
            entry["input_artifacts"] = _coerce_list(raw["inputs"])
        if "output_artifacts" not in entry and "associated_artifacts" in raw:
            entry["output_artifacts"] = _coerce_list(raw["associated_artifacts"])
        if "created_by_agent" not in entry and "created_by" in raw:
            entry["created_by_agent"] = raw["created_by"]
        return entry

    def _migrate_issue_entry(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entry = self._migrate_common_entry("issue_registry", raw)
        if "affected_artifacts" not in entry and "stale_artifacts" in raw:
            entry["affected_artifacts"] = _coerce_list(raw["stale_artifacts"])
        return entry

    def _migrate_source_entry(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        entry = self._migrate_common_entry("source_registry", raw)
        if "source" not in entry:
            entry["source"] = raw.get("original_path") or raw.get("url") or raw.get("title", "")
        if "topic" not in entry:
            topics = raw.get("topics")
            if isinstance(topics, list):
                entry["topic"] = ", ".join(str(t) for t in topics)
            else:
                entry["topic"] = str(topics or "")
        return entry

    def _atomic_write(self, path: Path, data: Dict[str, Any]) -> None:
        """Write JSON atomically: temp file -> fsync -> os.replace."""
        path.parent.mkdir(parents=True, exist_ok=True)
        # NamedTemporaryFile with delete=False so we control the rename.
        fd, tmp = tempfile.mkstemp(
            prefix=path.name + ".",
            suffix=".tmp",
            dir=str(path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ----- validation -----

    def validate(self, name: str) -> List[str]:
        """Validate a registry and return a list of issue strings. Empty list = ok."""
        data = self.load(name)
        issues: List[str] = []
        id_field = _REGISTRY_ID_FIELDS[name]
        cls = _REGISTRY_DATACLASSES[name]
        seen_ids: set[str] = set()
        for i, raw in enumerate(data.get("entries", [])):
            if not isinstance(raw, dict):
                issues.append(f"entry[{i}] is not an object")
                continue
            eid = raw.get(id_field)
            if not eid or not isinstance(eid, str):
                issues.append(f"entry[{i}] missing string {id_field}")
            elif eid in seen_ids:
                issues.append(f"entry[{i}] duplicate {id_field}={eid}")
            else:
                seen_ids.add(eid)
            # Construct dataclass instance to leverage its validator.
            try:
                instance = cls(**_filter_for_dataclass(name, raw))
                if hasattr(instance, "validate"):
                    instance.validate()
            except TypeError as e:
                issues.append(f"entry[{i}] shape error: {e}")
            except ValueError as e:
                issues.append(f"entry[{i}] vocab error: {e}")
        return issues

    # ----- mutations -----

    def next_id(self, name: str) -> str:
        """Generate the next sequential ID for this registry."""
        data = self.load(name)
        prefix = REGISTRY_ID_PREFIXES[name]
        id_field = _REGISTRY_ID_FIELDS[name]
        highest = 0
        for entry in data.get("entries", []):
            eid = entry.get(id_field, "")
            if eid.startswith(prefix + "-"):
                try:
                    n = int(eid.split("-", 1)[1])
                    if n > highest:
                        highest = n
                except ValueError:
                    continue
        return f"{prefix}-{highest + 1:04d}"

    def append(self, name: str, entry: Any) -> str:
        """Append an entry. Assigns an ID if missing. Returns the entry ID."""
        with self._lock:
            data = self.load(name)
            entry_dict = _to_dict(entry)
            id_field = _REGISTRY_ID_FIELDS[name]
            if not entry_dict.get(id_field):
                entry_dict[id_field] = self.next_id(name)
            now = _utc_now_iso()
            entry_dict.setdefault("created_at", now)
            entry_dict["updated_at"] = now

            # Reject duplicate IDs.
            existing_ids = {
                e.get(id_field) for e in data.get("entries", []) if isinstance(e, dict)
            }
            if entry_dict[id_field] in existing_ids:
                raise RegistryValidationError(
                    f"Duplicate {id_field}={entry_dict[id_field]} in {name}"
                )

            # Validate against dataclass.
            cls = _REGISTRY_DATACLASSES[name]
            try:
                instance = cls(**_filter_for_dataclass(name, entry_dict))
                if hasattr(instance, "validate"):
                    instance.validate()
            except (TypeError, ValueError) as e:
                raise RegistryValidationError(
                    f"Invalid entry for {name}: {e}"
                ) from e

            data["entries"].append(entry_dict)
            data["updated_at"] = now
            self._atomic_write(self.path_for(name), data)
            return entry_dict[id_field]

    def update(self, name: str, entry_id: str, patch: Dict[str, Any]) -> None:
        """Merge ``patch`` into the entry with ID ``entry_id``."""
        if not isinstance(patch, dict):
            raise TypeError("patch must be a dict")
        forbidden = set(patch) & {_REGISTRY_ID_FIELDS[name], "created_at"}
        if forbidden:
            raise RegistryValidationError(
                f"Patch cannot modify immutable fields: {sorted(forbidden)}"
            )
        with self._lock:
            data = self.load(name)
            id_field = _REGISTRY_ID_FIELDS[name]
            cls = _REGISTRY_DATACLASSES[name]
            updated = False
            for entry in data.get("entries", []):
                if entry.get(id_field) == entry_id:
                    merged = {**entry, **patch, "updated_at": _utc_now_iso()}
                    try:
                        instance = cls(**_filter_for_dataclass(name, merged))
                        if hasattr(instance, "validate"):
                            instance.validate()
                    except (TypeError, ValueError) as e:
                        raise RegistryValidationError(
                            f"Invalid update for {name} {entry_id}: {e}"
                        ) from e
                    entry.clear()
                    entry.update(merged)
                    updated = True
                    break
            if not updated:
                raise KeyError(f"{entry_id} not found in {name}")
            data["updated_at"] = _utc_now_iso()
            self._atomic_write(self.path_for(name), data)

    def get(self, name: str, entry_id: str) -> Optional[Dict[str, Any]]:
        data = self.load(name)
        id_field = _REGISTRY_ID_FIELDS[name]
        for entry in data.get("entries", []):
            if entry.get(id_field) == entry_id:
                return dict(entry)
        return None

    def find(self, name: str, predicate: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
        data = self.load(name)
        return [dict(e) for e in data.get("entries", []) if predicate(e)]

    def all_entries(self, name: str) -> List[Dict[str, Any]]:
        return [dict(e) for e in self.load(name).get("entries", [])]


def ensure_registries_initialized(store: RegistryStore) -> None:
    """Create all 7 empty registry files if they don't exist yet."""
    for name in REGISTRY_NAMES:
        path = store.path_for(name)
        if not path.exists():
            store._atomic_write(path, store._empty_registry(name))


__all__ = [
    "REGISTRY_NAMES",
    "REGISTRY_ID_PREFIXES",
    "RegistryStore",
    "RegistryValidationError",
    "ensure_registries_initialized",
]
