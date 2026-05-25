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


REGISTRY_NAMES: Tuple[str, ...] = (
    "artifact_registry",
    "claim_registry",
    "experiment_registry",
    "issue_registry",
    "source_registry",
    "environment_registry",
    "decision_registry",
)

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
        if not isinstance(data, dict) or "entries" not in data:
            raise RegistryValidationError(
                f"{path} is malformed; expected an object with an 'entries' list"
            )
        return data

    def _empty_registry(self, name: str) -> Dict[str, Any]:
        return {
            "registry": name,
            "id_prefix": REGISTRY_ID_PREFIXES[name],
            "created_at": _utc_now_iso(),
            "updated_at": _utc_now_iso(),
            "entries": [],
        }

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
                instance = cls(**raw)
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
                instance = cls(**entry_dict)
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
                        instance = cls(**merged)
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
