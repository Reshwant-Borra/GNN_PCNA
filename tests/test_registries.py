"""Registry atomic write, append, update, validate, dup-reject."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_os.registries.store import (
    REGISTRY_NAMES,
    RegistryStore,
    RegistryValidationError,
    ensure_registries_initialized,
)
from research_os.schemas.registries import ArtifactEntry, ClaimEntry


def test_initialize_creates_all_files(tmp_path):
    store = RegistryStore(tmp_path)
    ensure_registries_initialized(store)
    for name in REGISTRY_NAMES:
        assert store.path_for(name).exists()


def test_append_assigns_sequential_ids(tmp_registries):
    aid1 = tmp_registries.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="", path="/a", artifact_type="checkpoint", status="current"
        ),
    )
    aid2 = tmp_registries.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="", path="/b", artifact_type="checkpoint", status="current"
        ),
    )
    assert aid1 == "ART-0001"
    assert aid2 == "ART-0002"


def test_duplicate_id_rejected(tmp_registries):
    tmp_registries.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="ART-9999",
            path="/a",
            artifact_type="checkpoint",
            status="current",
        ),
    )
    with pytest.raises(RegistryValidationError):
        tmp_registries.append(
            "artifact_registry",
            {
                "artifact_id": "ART-9999",
                "path": "/b",
                "artifact_type": "checkpoint",
                "status": "current",
            },
        )


def test_update_merges_and_validates(tmp_registries):
    aid = tmp_registries.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="", path="/a", artifact_type="checkpoint", status="current"
        ),
    )
    tmp_registries.update("artifact_registry", aid, {"status": "stale", "status_reason": "bug fix"})
    entry = tmp_registries.get("artifact_registry", aid)
    assert entry["status"] == "stale"
    with pytest.raises(RegistryValidationError):
        tmp_registries.update("artifact_registry", aid, {"status": "magical"})


def test_update_cannot_change_id(tmp_registries):
    aid = tmp_registries.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="", path="/a", artifact_type="checkpoint", status="current"
        ),
    )
    with pytest.raises(RegistryValidationError):
        tmp_registries.update("artifact_registry", aid, {"artifact_id": "ART-9999"})


def test_atomic_write_does_not_leave_temp_files(tmp_registries):
    base = tmp_registries.base_dir
    tmp_registries.append(
        "claim_registry",
        ClaimEntry(
            claim_id="",
            claim_text="x",
            claim_strength="hypothesis_generating",
            status="hypothesis_generating",
        ),
    )
    leftovers = list(base.glob("*.tmp"))
    assert leftovers == []
    data = json.loads(base.joinpath("claim_registry.json").read_text(encoding="utf-8"))
    assert data["entries"][0]["claim_id"] == "CLAIM-0001"


def test_validate_returns_issue_for_bad_status(tmp_registries):
    # Mutate JSON on disk to inject a bad status.
    path = tmp_registries.path_for("artifact_registry")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["entries"].append(
        {
            "artifact_id": "ART-0099",
            "path": "/x",
            "artifact_type": "checkpoint",
            "status": "magical",
        }
    )
    path.write_text(json.dumps(data), encoding="utf-8")
    issues = tmp_registries.validate("artifact_registry")
    assert issues
    assert any("magical" in i for i in issues)
