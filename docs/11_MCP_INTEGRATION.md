# ResearchOS MCP Integration

ResearchOS exposes one project MCP server named `researchos`. Claude Code and Codex should use this server as the bridge into the existing ResearchOS orchestrator; do not bypass or replace the orchestrator.

## Project Config

The project-level `.mcp.json` should contain:

```json
{
  "mcpServers": {
    "researchos": {
      "type": "stdio",
      "command": "C:\\Users\\reshw\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
      "args": [
        "-m",
        "research_os.integrations.claude_code.mcp_server"
      ],
      "env": {
        "RESEARCH_OS_REPO": "."
      }
    }
  }
}
```

Run verification commands from:

```powershell
C:\Users\reshw\ResearchOS
```

## Verify In Claude Code

```powershell
claude mcp list
```

Expected result: a server named `researchos` is listed and points at the stdio command in `.mcp.json`.

Inside Claude Code:

```text
/mcp
```

Expected result: `researchos` appears with tools such as `route_request`, `run_request`, `run_workflow`, and `get_report`.

## Test Prompt

Use a low-risk routing prompt first:

```text
Use the ResearchOS MCP server to route this request: What is the current project status?
```

Expected behavior:

- Claude Code calls `researchos.route_request`.
- The MCP server starts `research_os.integrations.claude_code.mcp_server`.
- The tool response includes a ResearchOS route with selected agents, gates, and conversation guidance.
- If execution is appropriate, Claude Code can then call `researchos.run_request`, which routes through the ResearchOS orchestrator and writes a report.

## Direct Server Smoke Test

This checks that the stdio command starts and answers MCP JSON-RPC:

```powershell
'{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | C:\Users\reshw\AppData\Local\Programs\Python\Python311\python.exe -m research_os.integrations.claude_code.mcp_server
```

Expected result: JSON output containing `route_request`, `run_request`, `run_workflow`, `get_report`, `submit_compute_intent`, and `approve_or_deny`.
