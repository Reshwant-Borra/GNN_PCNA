"""Registry layer: append-only JSON stores with closed-vocabulary validation.

ResearchOS keeps machine-readable state in seven JSON registries:

    artifact_registry.json
    claim_registry.json
    experiment_registry.json
    issue_registry.json
    source_registry.json
    environment_registry.json
    decision_registry.json

Registries never destructively delete entries; status fields encode lifecycle.
All writes go through `RegistryStore` so they are atomic and validated.
"""

from research_os.registries.store import (
    REGISTRY_NAMES,
    REGISTRY_ID_PREFIXES,
    RegistryStore,
    RegistryValidationError,
    ensure_registries_initialized,
)

__all__ = [
    "REGISTRY_NAMES",
    "REGISTRY_ID_PREFIXES",
    "RegistryStore",
    "RegistryValidationError",
    "ensure_registries_initialized",
]
