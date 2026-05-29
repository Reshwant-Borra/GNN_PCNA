"""Memory loader and update protocol."""
from __future__ import annotations

import pytest

from research_os.memory.store import (
    CANONICAL_FILES,
    MemoryUpdateProposal,
    apply_memory_update,
)


def test_memory_initializes_with_all_canonical_files(tmp_memory):
    for name in CANONICAL_FILES:
        assert tmp_memory.exists(name)
        m = tmp_memory.read(name)
        assert m.title
        assert m.status in ("current", "needs_review", "stale")


def test_apply_safe_update(tmp_memory):
    p = MemoryUpdateProposal(
        target_file="CURRENT_CLAIMS.md",
        update_type="add_fact",
        summary="add documented baseline result",
        append_section="- documented baseline AUROC=0.6 on chain-blocked split",
    )
    m = apply_memory_update(tmp_memory, p, applied_by="test")
    assert "documented baseline" in m.body
    assert m.status == "current"


def test_apply_requires_human_approval_rejects(tmp_memory):
    p = MemoryUpdateProposal(
        target_file="CURRENT_CLAIMS.md",
        update_type="upgrade_claim",
        summary="upgrade to strongly supported",
        append_section="- strongly_supported_computationally",
        requires_human_approval=True,
        reason_human_approval_required="claim upgrade requires PI sign-off",
    )
    with pytest.raises(PermissionError):
        apply_memory_update(tmp_memory, p, applied_by="test")


def test_proposal_validates_target(tmp_memory):
    p = MemoryUpdateProposal(
        target_file="UNKNOWN_FILE.md",
        update_type="add_fact",
        summary="x",
        append_section="x",
    )
    with pytest.raises(ValueError):
        p.validate()


def test_proposal_validates_update_type(tmp_memory):
    p = MemoryUpdateProposal(
        target_file="CURRENT_CLAIMS.md",
        update_type="not_an_update_type",
        summary="x",
        append_section="x",
    )
    with pytest.raises(ValueError):
        p.validate()
