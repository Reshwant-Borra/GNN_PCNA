"""Tool registry for the autonomous-agent framework.

A ``Tool`` wraps a callable with:

- a stable ``name`` (referenced by ``AgentProfile.allowed_tools``)
- structured input/output schemas (dicts of {name: type-hint-string})
- an optional ``requires_env`` flag for opt-in tools
- a ``side_effect_class`` ("read" | "write" | "external" | "compute")
- the actual runner (callable)

Tools never mutate global state without going through the existing safety
layers (memory updates still flow through ``apply_memory_update``; registry
writes still go through ``RegistryStore.add_entry``).

The registry is just a dict keyed by name with safety checks — no hidden
state, no magic. Agents construct their own registry instance per run if
they need different tool sets.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional


# ---------------------------------------------------------------------------
# Tool + result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ToolResult:
    """Uniform result envelope for every tool call."""
    ok: bool
    tool_name: str
    output: Any = None
    error: str = ""
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def summary(self, max_chars: int = 240) -> str:
        if not self.ok:
            return f"[error: {self.error[:max_chars]}]"
        if isinstance(self.output, (str, int, float, bool)):
            return str(self.output)[:max_chars]
        if isinstance(self.output, (list, tuple)):
            return f"[{len(self.output)} items]"
        if isinstance(self.output, dict):
            keys = ", ".join(list(self.output.keys())[:5])
            return f"{{dict with keys: {keys}}}"
        return str(self.output)[:max_chars]


@dataclass
class Tool:
    """One registered capability."""
    name: str
    description: str
    runner: Callable[..., Any]
    inputs_schema: Dict[str, str] = field(default_factory=dict)
    outputs_schema: Dict[str, str] = field(default_factory=dict)
    requires_env: Optional[str] = None
    side_effect_class: str = "read"  # "read" | "write" | "external" | "compute"
    category: str = "general"

    def is_enabled(self) -> bool:
        if self.requires_env is None:
            return True
        return os.environ.get(self.requires_env, "").strip() in ("1", "true", "True", "yes", "on")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """A namespace of tools available for autonomous agents to call.

    The registry enforces:

    - **Unique names.** Re-registering a tool name raises.
    - **Env-var gates.** ``call()`` of a disabled tool returns a clean
      ``ToolResult(ok=False, error="tool disabled: <env>")`` rather than
      raising — the agent's planner can react.
    - **Allow-list checks.** ``call_for_profile()`` rejects tools that the
      caller's profile does not declare.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    # -- registration ---------------------------------------------------

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def register_many(self, tools: Iterable[Tool]) -> None:
        for t in tools:
            self.register(t)

    # -- introspection --------------------------------------------------

    def names(self) -> List[str]:
        return sorted(self._tools)

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)

    def describe(self) -> List[Dict[str, Any]]:
        out = []
        for t in sorted(self._tools.values(), key=lambda x: x.name):
            out.append({
                "name": t.name,
                "description": t.description,
                "inputs_schema": dict(t.inputs_schema),
                "outputs_schema": dict(t.outputs_schema),
                "requires_env": t.requires_env,
                "side_effect_class": t.side_effect_class,
                "category": t.category,
                "enabled": t.is_enabled(),
            })
        return out

    # -- invocation -----------------------------------------------------

    def call(self, name: str, inputs: Optional[Mapping[str, Any]] = None) -> ToolResult:
        """Invoke a tool by name. Always returns a ToolResult — never raises."""
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(ok=False, tool_name=name, error=f"unknown tool: {name}")
        if not tool.is_enabled():
            return ToolResult(
                ok=False,
                tool_name=name,
                error=f"tool disabled (set {tool.requires_env}=1 to enable)",
                metadata={"requires_env": tool.requires_env},
            )
        start = time.time()
        try:
            output = tool.runner(**(dict(inputs or {})))
        except TypeError as e:
            # Schema mismatch — surface as an error the planner can fix.
            return ToolResult(
                ok=False, tool_name=name,
                error=f"input mismatch: {e}",
                duration_seconds=time.time() - start,
            )
        except Exception as e:
            return ToolResult(
                ok=False, tool_name=name,
                error=f"{type(e).__name__}: {e}",
                duration_seconds=time.time() - start,
            )
        return ToolResult(
            ok=True, tool_name=name,
            output=output, duration_seconds=time.time() - start,
        )

    def call_for_profile(
        self,
        profile_allowed: Iterable[str],
        name: str,
        inputs: Optional[Mapping[str, Any]] = None,
    ) -> ToolResult:
        """Like ``call`` but rejects tools not on the profile's allow-list."""
        allowed = set(profile_allowed)
        if name not in allowed:
            return ToolResult(
                ok=False, tool_name=name,
                error=f"tool '{name}' not in agent profile allow-list",
            )
        return self.call(name, inputs)


__all__ = ["Tool", "ToolRegistry", "ToolResult"]
