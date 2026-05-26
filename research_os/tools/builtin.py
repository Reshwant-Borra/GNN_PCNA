"""Built-in tools that are always available to autonomous agents.

These are pure wrappers over existing infrastructure (``MemoryStore``,
``RegistryStore``, ``tools.git``, ``tools.hashing``, ``tools.environment``,
filesystem reads). They:

- never call the network,
- never write to disk except through the same safety layers existing agents
  use (``apply_memory_update``, ``RegistryStore.add_entry``),
- always return JSON-serializable values.

Registration:

    from research_os.tools.registry import ToolRegistry
    from research_os.tools.builtin import register_builtin
    reg = ToolRegistry()
    register_builtin(reg, ctx=agent_context)

After registration, ``reg.call("memory_read", {"name": "PROJECT_CANONICAL_STATUS.md"})``
returns the file body.
"""
from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from research_os.agents.base import AgentContext
from research_os.memory.store import (
    CANONICAL_FILES,
    MemoryStore,
    MemoryUpdateProposal,
    apply_memory_update,
)
from research_os.registries.store import RegistryStore
from research_os.tools.environment import capture_environment
from research_os.tools.git import capture_git_state
from research_os.tools.hashing import file_hash
from research_os.tools.registry import Tool, ToolRegistry


# ---------------------------------------------------------------------------
# Memory tools
# ---------------------------------------------------------------------------

def _memory_or_raise(ctx: AgentContext) -> MemoryStore:
    if ctx.memory_store is None:
        raise RuntimeError("AgentContext has no memory_store attached")
    return ctx.memory_store


def _mk_memory_read(ctx: AgentContext) -> Callable[..., Dict[str, Any]]:
    def runner(*, name: str) -> Dict[str, Any]:
        store = _memory_or_raise(ctx)
        if name not in CANONICAL_FILES:
            raise ValueError(
                f"'{name}' is not a canonical memory file. "
                f"Allowed: {list(CANONICAL_FILES)}"
            )
        if not store.exists(name):
            return {"name": name, "exists": False, "body": "", "status": "missing"}
        mem = store.read(name)
        return {
            "name": mem.name,
            "exists": True,
            "title": mem.title,
            "status": mem.status,
            "last_updated": mem.last_updated,
            "updated_by": mem.updated_by,
            "body": mem.body,
        }
    return runner


def _mk_memory_list(ctx: AgentContext) -> Callable[..., Dict[str, Any]]:
    def runner() -> Dict[str, Any]:
        store = ctx.memory_store
        out = []
        for name in CANONICAL_FILES:
            present = store is not None and store.exists(name)
            entry: Dict[str, Any] = {"name": name, "exists": present}
            if present and store is not None:
                try:
                    mem = store.read(name)
                    entry["status"] = mem.status
                    entry["last_updated"] = mem.last_updated
                except Exception as e:
                    entry["error"] = str(e)
            out.append(entry)
        return {"files": out}
    return runner


def _mk_memory_propose_update(ctx: AgentContext, *, agent_id: str) -> Callable[..., Dict[str, Any]]:
    def runner(
        *,
        target_file: str,
        update_type: str,
        summary: str,
        append_section: Optional[str] = None,
        section_heading: Optional[str] = None,
        new_body: Optional[str] = None,
        requires_human_approval: bool = False,
        reason_human_approval_required: str = "",
        evidence: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        store = _memory_or_raise(ctx)
        if append_section is None and new_body is None:
            raise ValueError("either append_section or new_body must be set")
        proposal = MemoryUpdateProposal(
            target_file=target_file,
            update_type=update_type,
            summary=summary,
            proposed_by=agent_id,
            new_body=new_body,
            append_section=append_section,
            section_heading=section_heading,
            evidence=list(evidence or []),
            requires_human_approval=requires_human_approval,
            reason_human_approval_required=reason_human_approval_required,
        )
        if requires_human_approval:
            # Surface — do NOT apply.
            return {
                "applied": False,
                "queued_for_human": True,
                "proposal": proposal.to_dict(),
            }
        mem = apply_memory_update(store, proposal, applied_by=agent_id)
        return {
            "applied": True,
            "queued_for_human": False,
            "target_file": mem.name,
            "status": mem.status,
            "last_updated": mem.last_updated,
        }
    return runner


# ---------------------------------------------------------------------------
# Registry tools
# ---------------------------------------------------------------------------

def _registry_or_raise(ctx: AgentContext) -> RegistryStore:
    if ctx.registry_store is None:
        raise RuntimeError("AgentContext has no registry_store attached")
    return ctx.registry_store


def _mk_registry_read(ctx: AgentContext) -> Callable[..., Dict[str, Any]]:
    def runner(*, name: str, limit: int = 200) -> Dict[str, Any]:
        store = _registry_or_raise(ctx)
        entries = store.all_entries(name)
        return {"registry": name, "count": len(entries), "entries": entries[:limit]}
    return runner


def _mk_registry_query(ctx: AgentContext) -> Callable[..., Dict[str, Any]]:
    def runner(*, name: str, field: str, value: Any) -> Dict[str, Any]:
        store = _registry_or_raise(ctx)
        matches = store.find(name, lambda e: e.get(field) == value)
        return {"registry": name, "field": field, "value": value, "matches": matches}
    return runner


# ---------------------------------------------------------------------------
# Filesystem tools
# ---------------------------------------------------------------------------

_SAFE_GLOB_EXCLUDES = {".git", "__pycache__", "research_os_memory",
                       "research_os_registries", "reports", "data", "node_modules"}


def _mk_file_read(ctx: AgentContext) -> Callable[..., Dict[str, Any]]:
    def runner(*, path: str, max_bytes: int = 65536) -> Dict[str, Any]:
        repo_root = Path(ctx.repo_root).resolve()
        target = (repo_root / path).resolve()
        try:
            target.relative_to(repo_root)
        except ValueError:
            raise ValueError(f"path escapes repo root: {path}")
        if not target.exists():
            return {"path": path, "exists": False, "text": ""}
        if not target.is_file():
            return {"path": path, "exists": False, "text": "", "error": "not a file"}
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return {"path": path, "exists": True, "text": "", "error": str(e)}
        truncated = len(text.encode("utf-8")) > max_bytes
        if truncated:
            text = text[:max_bytes]
        return {
            "path": path,
            "exists": True,
            "size_bytes": target.stat().st_size,
            "truncated": truncated,
            "text": text,
        }
    return runner


def _mk_glob(ctx: AgentContext) -> Callable[..., Dict[str, Any]]:
    def runner(*, pattern: str, limit: int = 200) -> Dict[str, Any]:
        repo_root = Path(ctx.repo_root).resolve()
        results: List[str] = []
        for path in repo_root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(repo_root)
            if any(part in _SAFE_GLOB_EXCLUDES for part in rel.parts):
                continue
            if any(part.startswith(".") for part in rel.parts):
                continue
            rel_posix = rel.as_posix()
            if fnmatch.fnmatch(rel_posix, pattern) or fnmatch.fnmatch(rel.name, pattern):
                results.append(rel_posix)
                if len(results) >= limit:
                    break
        return {"pattern": pattern, "count": len(results), "matches": results}
    return runner


# ---------------------------------------------------------------------------
# State capture tools
# ---------------------------------------------------------------------------

def _mk_git_state(ctx: AgentContext) -> Callable[..., Dict[str, Any]]:
    def runner() -> Dict[str, Any]:
        return capture_git_state(Path(ctx.repo_root)).to_dict()
    return runner


def _mk_env_snapshot(ctx: AgentContext) -> Callable[..., Dict[str, Any]]:
    def runner() -> Dict[str, Any]:
        return capture_environment().to_dict()
    return runner


def _mk_hash_file(ctx: AgentContext) -> Callable[..., Dict[str, Any]]:
    def runner(*, path: str) -> Dict[str, Any]:
        repo_root = Path(ctx.repo_root).resolve()
        target = (repo_root / path).resolve()
        try:
            target.relative_to(repo_root)
        except ValueError:
            raise ValueError(f"path escapes repo root: {path}")
        if not target.exists() or not target.is_file():
            return {"path": path, "exists": False, "sha256": ""}
        return {"path": path, "exists": True, "sha256": file_hash(target)}
    return runner


# ---------------------------------------------------------------------------
# Public registration
# ---------------------------------------------------------------------------

def register_builtin(registry: ToolRegistry, ctx: AgentContext, *, agent_id: str = "") -> None:
    """Register all built-in tools bound to a given AgentContext + agent_id."""
    tools = [
        Tool(
            name="memory_read",
            description="Read one canonical memory file's body + metadata.",
            runner=_mk_memory_read(ctx),
            inputs_schema={"name": "str (one of CANONICAL_FILES)"},
            outputs_schema={"name": "str", "body": "str", "status": "str"},
            side_effect_class="read",
            category="memory",
        ),
        Tool(
            name="memory_list",
            description="List the 9 canonical memory files with presence + status.",
            runner=_mk_memory_list(ctx),
            outputs_schema={"files": "list[dict]"},
            side_effect_class="read",
            category="memory",
        ),
        Tool(
            name="memory_propose_update",
            description=(
                "Propose a structured update to a canonical memory file. Applied "
                "immediately unless requires_human_approval=True."
            ),
            runner=_mk_memory_propose_update(ctx, agent_id=agent_id or "autonomous_agent"),
            inputs_schema={
                "target_file": "str", "update_type": "str", "summary": "str",
                "append_section": "str?", "section_heading": "str?",
                "new_body": "str?", "requires_human_approval": "bool?",
                "evidence": "list[str]?",
            },
            outputs_schema={"applied": "bool", "queued_for_human": "bool"},
            side_effect_class="write",
            category="memory",
        ),
        Tool(
            name="registry_read",
            description="Return all entries from a named JSON registry (capped).",
            runner=_mk_registry_read(ctx),
            inputs_schema={"name": "str", "limit": "int?"},
            outputs_schema={"registry": "str", "count": "int", "entries": "list[dict]"},
            side_effect_class="read",
            category="registry",
        ),
        Tool(
            name="registry_query",
            description="Find registry entries where entry[field] == value.",
            runner=_mk_registry_query(ctx),
            inputs_schema={"name": "str", "field": "str", "value": "any"},
            outputs_schema={"matches": "list[dict]"},
            side_effect_class="read",
            category="registry",
        ),
        Tool(
            name="file_read",
            description="Read a UTF-8 file relative to repo root (sandboxed; truncated to max_bytes).",
            runner=_mk_file_read(ctx),
            inputs_schema={"path": "str", "max_bytes": "int?"},
            outputs_schema={"path": "str", "exists": "bool", "text": "str", "truncated": "bool"},
            side_effect_class="read",
            category="filesystem",
        ),
        Tool(
            name="glob",
            description="Find files matching a glob pattern under the repo root.",
            runner=_mk_glob(ctx),
            inputs_schema={"pattern": "str", "limit": "int?"},
            outputs_schema={"matches": "list[str]", "count": "int"},
            side_effect_class="read",
            category="filesystem",
        ),
        Tool(
            name="git_state",
            description="Snapshot git branch, HEAD, dirty status, modified/untracked counts.",
            runner=_mk_git_state(ctx),
            outputs_schema={"branch": "str", "short_commit": "str", "dirty": "bool"},
            side_effect_class="read",
            category="provenance",
        ),
        Tool(
            name="env_snapshot",
            description="Capture Python version, OS, key package versions, and GPU info if available.",
            runner=_mk_env_snapshot(ctx),
            outputs_schema={"python_version": "str", "os": "str"},
            side_effect_class="read",
            category="provenance",
        ),
        Tool(
            name="hash_file",
            description="Compute the SHA-256 of a file relative to repo root.",
            runner=_mk_hash_file(ctx),
            inputs_schema={"path": "str"},
            outputs_schema={"sha256": "str", "exists": "bool"},
            side_effect_class="read",
            category="provenance",
        ),
    ]
    registry.register_many(tools)


__all__ = ["register_builtin"]
