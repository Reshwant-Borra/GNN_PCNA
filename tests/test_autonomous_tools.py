"""Tests for the autonomous-framework ToolRegistry + built-in tools.

Covers:
- registration uniqueness
- env-var gating returns clean ToolResult (does not raise)
- profile allow-list rejection returns clean ToolResult
- built-in tools wired to AgentContext work end-to-end
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from research_os.agents.base import AgentContext
from research_os.memory.store import MemoryStore, ensure_memory_initialized
from research_os.registries.store import RegistryStore, ensure_registries_initialized
from research_os.tools.builtin import register_builtin
from research_os.tools.llm import register_llm, set_llm_backend, llm_enabled
from research_os.tools.registry import Tool, ToolRegistry, ToolResult
from research_os.tools.web import register_web, web_enabled


# ---------------------------------------------------------------------------
# Registry basics
# ---------------------------------------------------------------------------

def test_registry_register_and_describe():
    r = ToolRegistry()
    r.register(Tool(name="echo", description="echo input", runner=lambda **k: dict(k)))
    assert "echo" in r
    assert r.get("echo") is not None
    described = r.describe()
    assert len(described) == 1
    assert described[0]["name"] == "echo"
    assert described[0]["enabled"] is True


def test_registry_duplicate_registration_raises():
    r = ToolRegistry()
    r.register(Tool(name="x", description="x", runner=lambda: None))
    with pytest.raises(ValueError):
        r.register(Tool(name="x", description="x2", runner=lambda: None))


def test_registry_unknown_tool_returns_clean_error():
    r = ToolRegistry()
    res = r.call("missing", {})
    assert isinstance(res, ToolResult)
    assert res.ok is False
    assert "unknown" in res.error


def test_registry_env_gated_tool_returns_clean_error(monkeypatch):
    r = ToolRegistry()
    r.register(Tool(
        name="gated", description="g", runner=lambda: "ran",
        requires_env="ENABLE_FAKE_TOOL",
    ))
    monkeypatch.delenv("ENABLE_FAKE_TOOL", raising=False)
    res = r.call("gated", {})
    assert res.ok is False
    assert "disabled" in res.error
    assert res.metadata["requires_env"] == "ENABLE_FAKE_TOOL"

    monkeypatch.setenv("ENABLE_FAKE_TOOL", "1")
    res2 = r.call("gated", {})
    assert res2.ok is True
    assert res2.output == "ran"


def test_registry_input_mismatch_returns_clean_error():
    r = ToolRegistry()

    def runner(*, expected: str) -> str:
        return expected.upper()

    r.register(Tool(name="upper", description="x", runner=runner))
    res = r.call("upper", {"wrong_kw": "x"})
    assert res.ok is False
    assert "input mismatch" in res.error


def test_registry_runner_exception_returns_clean_error():
    r = ToolRegistry()

    def runner() -> None:
        raise RuntimeError("boom")

    r.register(Tool(name="bomb", description="x", runner=runner))
    res = r.call("bomb", {})
    assert res.ok is False
    assert "RuntimeError: boom" in res.error


def test_call_for_profile_rejects_unlisted_tool():
    r = ToolRegistry()
    r.register(Tool(name="allowed", description="x", runner=lambda: 1))
    r.register(Tool(name="forbidden", description="x", runner=lambda: 1))
    res = r.call_for_profile(["allowed"], "forbidden", {})
    assert res.ok is False
    assert "not in agent profile allow-list" in res.error


# ---------------------------------------------------------------------------
# Built-in tools end-to-end
# ---------------------------------------------------------------------------

@pytest.fixture
def wired_ctx(tmp_path: Path) -> AgentContext:
    mem = MemoryStore(tmp_path / "mem")
    ensure_memory_initialized(mem)
    reg = RegistryStore(tmp_path / "reg")
    ensure_registries_initialized(reg)
    return AgentContext(repo_root=tmp_path, memory_store=mem, registry_store=reg)


def test_builtin_memory_read(wired_ctx: AgentContext):
    r = ToolRegistry()
    register_builtin(r, wired_ctx, agent_id="test_agent")
    res = r.call("memory_read", {"name": "PROJECT_CANONICAL_STATUS.md"})
    assert res.ok is True
    assert res.output["exists"] is True
    assert "Project goal" in res.output["body"]


def test_builtin_memory_read_rejects_non_canonical(wired_ctx: AgentContext):
    r = ToolRegistry()
    register_builtin(r, wired_ctx, agent_id="test_agent")
    res = r.call("memory_read", {"name": "not_canonical.md"})
    assert res.ok is False
    assert "not a canonical memory file" in res.error


def test_builtin_memory_list(wired_ctx: AgentContext):
    r = ToolRegistry()
    register_builtin(r, wired_ctx, agent_id="test_agent")
    res = r.call("memory_list", {})
    assert res.ok is True
    names = [f["name"] for f in res.output["files"]]
    assert "PROJECT_CANONICAL_STATUS.md" in names


def test_builtin_memory_propose_update_writes(wired_ctx: AgentContext):
    r = ToolRegistry()
    register_builtin(r, wired_ctx, agent_id="test_agent")
    res = r.call("memory_propose_update", {
        "target_file": "HUMAN_DECISIONS.md",
        "update_type": "add_human_decision",
        "summary": "Test decision",
        "append_section": "- DEC-TEST: a test decision",
    })
    assert res.ok is True
    assert res.output["applied"] is True
    # Confirm the file was actually updated.
    body = wired_ctx.memory_store.read("HUMAN_DECISIONS.md").body  # type: ignore[union-attr]
    assert "DEC-TEST" in body


def test_builtin_memory_propose_update_queues_when_human_required(wired_ctx: AgentContext):
    r = ToolRegistry()
    register_builtin(r, wired_ctx, agent_id="test_agent")
    res = r.call("memory_propose_update", {
        "target_file": "CURRENT_CLAIMS.md",
        "update_type": "upgrade_claim",
        "summary": "Test claim upgrade",
        "append_section": "(test)",
        "requires_human_approval": True,
        "reason_human_approval_required": "Upgrades above moderately_supported need PI.",
    })
    assert res.ok is True
    assert res.output["applied"] is False
    assert res.output["queued_for_human"] is True


def test_builtin_registry_read(wired_ctx: AgentContext):
    r = ToolRegistry()
    register_builtin(r, wired_ctx, agent_id="test_agent")
    res = r.call("registry_read", {"name": "artifact_registry"})
    assert res.ok is True
    assert "registry" in res.output


def test_builtin_glob_sandboxed_to_repo(wired_ctx: AgentContext, tmp_path: Path):
    (tmp_path / "foo.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "bar.md").write_text("md", encoding="utf-8")
    r = ToolRegistry()
    register_builtin(r, wired_ctx, agent_id="test_agent")
    res = r.call("glob", {"pattern": "*.txt"})
    assert res.ok is True
    assert any(p.endswith("foo.txt") for p in res.output["matches"])


def test_builtin_file_read_blocks_path_escape(wired_ctx: AgentContext, tmp_path: Path):
    r = ToolRegistry()
    register_builtin(r, wired_ctx, agent_id="test_agent")
    res = r.call("file_read", {"path": "../etc/passwd"})
    assert res.ok is False
    assert "escapes repo root" in res.error


# ---------------------------------------------------------------------------
# Web / LLM env-gated by default
# ---------------------------------------------------------------------------

def test_web_disabled_by_default(monkeypatch):
    monkeypatch.delenv("RESEARCHOS_ENABLE_WEB", raising=False)
    r = ToolRegistry()
    register_web(r)
    assert web_enabled() is False
    res = r.call("web_fetch", {"url": "https://example.com"})
    assert res.ok is False
    assert "disabled" in res.error


def test_llm_disabled_by_default(monkeypatch):
    monkeypatch.delenv("RESEARCHOS_ENABLE_LLM_AGENTS", raising=False)
    r = ToolRegistry()
    register_llm(r)
    assert llm_enabled() is False
    res = r.call("llm_chat", {"system": "s", "user": "u"})
    assert res.ok is False
    assert "disabled" in res.error


def test_llm_with_injected_backend(monkeypatch):
    monkeypatch.setenv("RESEARCHOS_ENABLE_LLM_AGENTS", "1")

    def fake_backend(system: str, user: str, timeout_s: float) -> str:
        return f'{{"echo": "{user[:20]}"}}'

    set_llm_backend(fake_backend)
    try:
        r = ToolRegistry()
        register_llm(r)
        res = r.call("llm_chat", {"system": "you are X", "user": "hello world",
                                   "expect_json": True})
        assert res.ok is True
        assert res.output["json"] == {"echo": "hello world"}
    finally:
        set_llm_backend(None)


def test_llm_falls_back_cleanly_on_backend_exception(monkeypatch):
    """The llm_chat tool catches backend exceptions internally and returns
    a structured ``{ok: False, error: ...}`` envelope. The outer
    ToolResult.ok is True because the tool itself didn't crash — the
    distinction lets callers tell apart "tool is broken" from "tool ran
    and reported failure"."""
    monkeypatch.setenv("RESEARCHOS_ENABLE_LLM_AGENTS", "1")

    def broken(system: str, user: str, timeout_s: float) -> str:
        raise OSError("connection refused")

    set_llm_backend(broken)
    try:
        r = ToolRegistry()
        register_llm(r)
        res = r.call("llm_chat", {"system": "s", "user": "u"})
        assert res.ok is True                       # tool itself ran
        assert res.output["ok"] is False            # envelope reports failure
        assert "connection refused" in res.output["error"]
    finally:
        set_llm_backend(None)
