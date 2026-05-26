"""Dependency-free MCP stdio server for Claude Code.

Claude Code starts this module from `.mcp.json`. The server exposes ResearchOS
as tools while keeping stdout reserved for MCP protocol frames.
"""
from __future__ import annotations

import json
import sys
import traceback
from typing import Any, Dict

from research_os.integrations.claude_code.service import TOOLS


SERVER_NAME = "researchos"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"


TOOL_DEFS = [
    {
        "name": "route_request",
        "description": "Route a Claude prompt through ResearchOS without executing agents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "repo_root": {"type": "string"},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "run_request",
        "description": "Route and execute a Claude prompt through ResearchOS agents, writing a report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "repo_root": {"type": "string"},
                "force_if_human_required": {"type": "boolean", "default": False},
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "run_workflow",
        "description": "Run a named ResearchOS workflow such as full_audit or claim_audit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "args": {"type": "object"},
                "repo_root": {"type": "string"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "get_report",
        "description": "Return a compact summary for a ResearchOS report path or id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path_or_id": {"type": "string"},
                "repo_root": {"type": "string"},
                "max_chars": {"type": "integer", "default": 4000},
            },
            "required": ["path_or_id"],
        },
    },
    {
        "name": "submit_compute_intent",
        "description": "Submit an optional compute intent through the existing ResearchOS task dispatcher.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {"type": "string"},
                "args": {"type": "object"},
                "user": {"type": "string", "default": "claude"},
                "role": {
                    "type": "string",
                    "enum": ["viewer", "collaborator", "owner"],
                    "default": "collaborator",
                },
                "auto_approve": {"type": "boolean", "default": False},
            },
            "required": ["intent"],
        },
    },
    {
        "name": "approve_or_deny",
        "description": "Approve or deny a pending compute task in the current MCP process.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "decision": {"type": "string", "enum": ["approve", "deny"]},
                "user": {"type": "string", "default": "claude"},
                "reason": {"type": "string"},
            },
            "required": ["task_id", "decision"],
        },
    },
    {
        "name": "pursue_goal",
        "description": (
            "Run an autonomous campaign for a high-level goal. The controller "
            "decomposes the goal into sub-goals, dispatches them across the "
            "migrated AutonomousAgent variants, optionally runs the multi-agent "
            "verification suite, and returns a compact CampaignResult."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "objective": {"type": "string"},
                "rationale": {"type": "string"},
                "repo_root": {"type": "string"},
                "budget": {
                    "type": "object",
                    "description": "Optional Budget kwargs (max_iterations, max_tool_calls, max_failures, max_seconds, max_tokens).",
                    "additionalProperties": True,
                },
                "sub_goals": {
                    "type": "array",
                    "description": "Optional pre-decomposed sub-goals; each is {objective, rationale?, inputs?}.",
                    "items": {"type": "object"},
                },
                "heal_first": {"type": "boolean", "default": False},
                "heal_dry_run": {"type": "boolean", "default": True},
                "run_verification": {"type": "boolean", "default": True},
            },
            "required": ["objective"],
        },
    },
]


def _read_message() -> Dict[str, Any] | None:
    first = sys.stdin.buffer.readline()
    if not first:
        return None
    first_text = first.decode("utf-8", errors="replace").strip()
    if not first_text:
        return _read_message()
    if first_text.lower().startswith("content-length:"):
        length = int(first_text.split(":", 1)[1].strip())
        while True:
            line = sys.stdin.buffer.readline()
            if line in (b"\r\n", b"\n", b""):
                break
        body = sys.stdin.buffer.read(length)
        return json.loads(body.decode("utf-8"))
    return json.loads(first_text)


def _write_message(message: Dict[str, Any]) -> None:
    body = json.dumps(message, separators=(",", ":"), default=str).encode("utf-8")
    sys.stdout.buffer.write(body + b"\n")
    sys.stdout.buffer.flush()


def _result(request_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    payload = {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
    if data is not None:
        payload["error"]["data"] = data
    return payload


def _call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if name not in TOOLS:
        raise ValueError(f"unknown tool: {name}")
    if name == "run_workflow":
        result = TOOLS[name](
            name=arguments["name"],
            args=arguments.get("args") or {},
            repo_root=arguments.get("repo_root"),
        )
    else:
        result = TOOLS[name](**arguments)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2, default=str),
            }
        ],
        "isError": result.get("status") == "error",
    }


def _handle(message: Dict[str, Any]) -> Dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if method and method.startswith("notifications/"):
        return None
    if method == "initialize":
        return _result(
            request_id,
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )
    if method == "ping":
        return _result(request_id, {})
    if method == "tools/list":
        return _result(request_id, {"tools": TOOL_DEFS})
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            return _result(
                request_id,
                _call_tool(params.get("name", ""), params.get("arguments") or {}),
            )
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            return _error(request_id, -32000, str(exc))
    if method in ("resources/list", "prompts/list"):
        key = "resources" if method == "resources/list" else "prompts"
        return _result(request_id, {key: []})
    return _error(request_id, -32601, f"method not found: {method}")


def main() -> int:
    while True:
        try:
            message = _read_message()
        except Exception as exc:
            traceback.print_exc(file=sys.stderr)
            _write_message(_error(None, -32700, f"parse error: {exc}"))
            continue
        if message is None:
            return 0
        response = _handle(message)
        if response is not None:
            _write_message(response)


if __name__ == "__main__":
    raise SystemExit(main())
