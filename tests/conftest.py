"""Shared pytest fixtures for ResearchOS."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Disable real Ollama calls in the test process. The semantic-routing tests
# inject their own fake backends; everything else uses the deterministic
# keyword path.
os.environ.setdefault("RESEARCHOS_DISABLE_SEMANTIC", "1")

from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.orchestrator import Orchestrator
from research_os.registries.store import RegistryStore, ensure_registries_initialized


@pytest.fixture
def tmp_memory(tmp_path: Path) -> MemoryStore:
    store = MemoryStore(tmp_path / "mem")
    ensure_memory_initialized(store)
    return store


@pytest.fixture
def tmp_registries(tmp_path: Path) -> RegistryStore:
    store = RegistryStore(tmp_path / "reg")
    ensure_registries_initialized(store)
    return store


@pytest.fixture
def tmp_orchestrator(tmp_path: Path) -> Orchestrator:
    orch = Orchestrator(
        repo_root=tmp_path,
        memory_dir=tmp_path / "mem",
        registries_dir=tmp_path / "reg",
        reports_dir=tmp_path / "reports",
    )
    orch.bootstrap()
    return orch
