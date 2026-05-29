"""Stale propagation: downstream artifacts should be marked stale when upstream changes."""
from __future__ import annotations

import pytest

from research_os.schemas.registries import ArtifactEntry
from research_os.tools.dependency_graph import direct_downstream, propagate_stale


def _seed(registry):
    graphs = registry.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="",
            path="/data/graphs",
            artifact_type="graph",
            status="current",
        ),
    )
    ckpt = registry.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="",
            path="/ckpt/best.pt",
            artifact_type="checkpoint",
            status="current",
            dependencies=[graphs],
        ),
    )
    metrics = registry.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="",
            path="/results/metrics.json",
            artifact_type="metric",
            status="current",
            dependencies=[ckpt],
        ),
    )
    figure = registry.append(
        "artifact_registry",
        ArtifactEntry(
            artifact_id="",
            path="/results/figure.png",
            artifact_type="figure",
            status="current",
            dependencies=[metrics],
        ),
    )
    return graphs, ckpt, metrics, figure


def test_propagate_marks_all_downstream_stale(tmp_registries):
    graphs, ckpt, metrics, figure = _seed(tmp_registries)
    moved = propagate_stale(tmp_registries, [graphs], reason="graph builder bug fix")
    assert ckpt in moved
    assert metrics in moved
    assert figure in moved
    for aid in (ckpt, metrics, figure):
        assert tmp_registries.get("artifact_registry", aid)["status"] == "stale"


def test_propagate_does_not_revive_invalid(tmp_registries):
    graphs, ckpt, metrics, figure = _seed(tmp_registries)
    tmp_registries.update("artifact_registry", ckpt, {"status": "invalid", "status_reason": "wrong labels"})
    moved = propagate_stale(tmp_registries, [graphs], reason="graph rebuild")
    # The ckpt was invalid; we should not downgrade it to stale, but we should still
    # propagate to its descendants.
    assert tmp_registries.get("artifact_registry", ckpt)["status"] == "invalid"
    assert metrics in moved
    assert figure in moved


def test_direct_downstream_lookup(tmp_registries):
    graphs, ckpt, metrics, figure = _seed(tmp_registries)
    downstream = direct_downstream(tmp_registries, graphs)
    assert any(d["artifact_id"] == ckpt for d in downstream)
