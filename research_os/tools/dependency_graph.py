"""Stale-propagation graph for the artifact registry.

When a node (artifact ID, file path, or symbolic source) changes, every
artifact downstream of it should be marked stale. The graph is encoded inside
the artifact registry itself via the `dependencies` and `downstream_artifacts`
fields, plus the canonical stale triggers listed in
docs/memory/STALE_ARTIFACT_POLICY.md.
"""
from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Set

from research_os.registries.store import RegistryStore


def direct_downstream(
    store: RegistryStore, artifact_id: str
) -> List[Dict[str, object]]:
    """Return artifacts that directly depend on ``artifact_id``."""
    return store.find(
        "artifact_registry",
        lambda e: artifact_id in (e.get("dependencies") or []),
    )


def propagate_stale(
    store: RegistryStore,
    changed_artifact_ids: Iterable[str],
    *,
    reason: str,
    updated_by: str = "research_os.provenance",
) -> List[str]:
    """BFS over the artifact registry, marking every downstream artifact stale.

    Returns the list of artifact IDs that were transitioned to ``stale``.
    Already-stale / invalid / superseded artifacts are skipped (status downgrade
    only flows in one direction).
    """
    visited: Set[str] = set()
    transitioned: List[str] = []
    queue: deque[str] = deque(changed_artifact_ids)
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        for downstream in direct_downstream(store, current):
            aid = downstream.get("artifact_id")
            if not aid:
                continue
            status = downstream.get("status")
            if status in ("stale", "invalid", "superseded"):
                queue.append(aid)
                continue
            store.update(
                "artifact_registry",
                aid,
                {
                    "status": "stale",
                    "status_reason": f"upstream change: {reason} (from {current})",
                },
            )
            transitioned.append(aid)
            queue.append(aid)
    return transitioned


__all__ = ["direct_downstream", "propagate_stale"]
