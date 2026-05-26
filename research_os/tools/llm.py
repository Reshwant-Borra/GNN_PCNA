"""LLM tool for autonomous agents — opt-in via RESEARCHOS_ENABLE_LLM_AGENTS=1.

Reuses the same Ollama HTTP plumbing the semantic router and intent parser
already use, so there's only one place to configure the LLM backend
(``OLLAMA_HOST``, ``RESEARCHOS_OLLAMA_MODEL``).

Always falls back gracefully: if Ollama is unreachable, the tool returns
``{"ok": False, "error": "..."}`` instead of raising, so the autonomous
loop reverts to deterministic behavior.

Test backends:

    ctx_backend = StubLLM(lambda system, user: '{"plan": [...]}')
    set_llm_backend(ctx_backend)

This is the same dependency-injection pattern the semantic router uses.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Optional, Protocol

from research_os.tools.registry import Tool, ToolRegistry


_LLM_ENV = "RESEARCHOS_ENABLE_LLM_AGENTS"
_DEFAULT_MODEL = os.environ.get("RESEARCHOS_OLLAMA_MODEL", "gemma3:4b")
_DEFAULT_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
_DEFAULT_TIMEOUT = float(os.environ.get("RESEARCHOS_OLLAMA_TIMEOUT", "20"))


class LLMBackend(Protocol):
    def __call__(self, system: str, user: str, timeout_s: float) -> str: ...


_backend: Optional[LLMBackend] = None


def set_llm_backend(backend: Optional[LLMBackend]) -> None:
    """Inject a fake backend (tests). Pass None to revert to real Ollama."""
    global _backend
    _backend = backend


def _ollama_chat(system: str, user: str, timeout_s: float = _DEFAULT_TIMEOUT) -> str:
    """Default backend: local Ollama /api/chat."""
    endpoint = f"{_DEFAULT_HOST.rstrip('/')}/api/chat"
    payload = json.dumps({
        "model": _DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0},
    }).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read()
    parsed = json.loads(raw)
    msg = parsed.get("message") or {}
    content = msg.get("content")
    if not isinstance(content, str):
        raise OSError("Ollama response missing message.content")
    return content


def _llm_chat(*, system: str, user: str, timeout_s: float = _DEFAULT_TIMEOUT,
              expect_json: bool = False) -> Dict[str, Any]:
    backend = _backend or _ollama_chat
    try:
        text = backend(system=system, user=user, timeout_s=timeout_s) \
            if _accepts_kwargs(backend) else backend(system, user, timeout_s)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "text": ""}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "text": ""}
    result: Dict[str, Any] = {"ok": True, "text": text}
    if expect_json:
        parsed = _extract_json(text)
        result["json"] = parsed
        if parsed is None:
            result["ok"] = False
            result["error"] = "expected JSON but model returned no parseable object"
    return result


def _accepts_kwargs(fn: Callable) -> bool:
    """Detect whether a backend uses keyword-only signature (test stubs) or
    positional (the default ``_ollama_chat``)."""
    try:
        import inspect
        sig = inspect.signature(fn)
        return any(p.kind == inspect.Parameter.KEYWORD_ONLY
                   for p in sig.parameters.values())
    except (TypeError, ValueError):
        return False


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Pull the first top-level JSON object from model output."""
    s = (text or "").strip()
    s = s.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    # Find first {...} block, balanced.
    start = s.find("{")
    if start < 0:
        return None
    depth = 0
    for i, ch in enumerate(s[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(s[start:i + 1])
                    return obj if isinstance(obj, dict) else None
                except json.JSONDecodeError:
                    return None
    return None


def register_llm(registry: ToolRegistry) -> None:
    """Register the llm_chat tool. Gated by RESEARCHOS_ENABLE_LLM_AGENTS=1."""
    registry.register(Tool(
        name="llm_chat",
        description=(
            "Call the local Ollama model with a system + user prompt. "
            "Set expect_json=True to extract a balanced JSON object."
        ),
        runner=_llm_chat,
        inputs_schema={
            "system": "str", "user": "str",
            "timeout_s": "float?", "expect_json": "bool?",
        },
        outputs_schema={"ok": "bool", "text": "str", "json": "dict?"},
        requires_env=_LLM_ENV,
        side_effect_class="external",
        category="llm",
    ))


def llm_enabled() -> bool:
    return os.environ.get(_LLM_ENV, "").strip() in ("1", "true", "True", "yes", "on")


__all__ = ["register_llm", "set_llm_backend", "llm_enabled", "LLMBackend"]
