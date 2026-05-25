"""Claude Code integration tests."""
from __future__ import annotations

import json
from pathlib import Path

from research_os.integrations.claude_code import mcp_server
from research_os.integrations.claude_code.service import (
    get_report,
    route_request,
    run_request,
    run_named_workflow,
)


def test_route_request_detects_multi_agent_claim(tmp_path: Path):
    result = route_request(
        "Can we say MD validated the cryptic pocket?",
        repo_root=tmp_path,
    )
    plan = result["plan"]
    assert result["status"] == "routed"
    assert "claim_or_paper" in plan["intents"]
    assert "validation_skeptic" in plan["selected_agents"]
    assert "contradiction_hunter" in plan["selected_agents"]
    assert result["conversation_guidance"]["should_run_researchos"]


def test_run_request_writes_report(tmp_path: Path):
    result = run_request("What is the current project status?", repo_root=tmp_path)
    assert result["status"] == "completed"
    report = Path(result["report"]["markdown"])
    assert report.exists()
    assert result["summary"]["selected_agents"]


def test_run_request_holds_for_human_approval(tmp_path: Path):
    result = run_request("Submit the manuscript.", repo_root=tmp_path)
    assert result["status"] == "approval_required"
    assert result["summary"]["human_review_required"]


def test_run_named_workflow_and_get_report(tmp_path: Path):
    result = run_named_workflow("metric_verification", repo_root=tmp_path)
    assert result["status"] == "completed"
    found = get_report(result["report"]["base"], repo_root=tmp_path)
    assert found["status"] == "found"
    assert found["summary"]["selected_agents"]


def test_mcp_tools_list():
    response = mcp_server._handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    names = {tool["name"] for tool in response["result"]["tools"]}
    assert {"route_request", "run_request", "run_workflow"}.issubset(names)


def test_project_mcp_config_registers_researchos():
    config_path = Path(__file__).resolve().parents[1] / ".mcp.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    server = data["mcpServers"]["researchos"]
    assert server["type"] == "stdio"
    assert server["args"] == ["-m", "research_os.integrations.claude_code.mcp_server"]
    assert server["env"]["RESEARCH_OS_REPO"] == "."


def test_mcp_route_tool_call(tmp_path: Path):
    response = mcp_server._handle(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "route_request",
                "arguments": {
                    "prompt": "What is the latest AUROC?",
                    "repo_root": str(tmp_path),
                },
            },
        }
    )
    assert response is not None
    text = response["result"]["content"][0]["text"]
    payload = json.loads(text)
    assert payload["status"] == "routed"
    assert "metric_verification" in payload["plan"]["intents"]
