"""ResearchOS monitoring dashboard — FastAPI backend.

Start via:  python dashboard/start.py
            python dashboard/start.py --port 7765 --repo-root .
"""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

# Module-level config — patched by start.py before uvicorn imports this module.
REPO_ROOT: Path = Path(".")

app = FastAPI(title="ResearchOS Dashboard", docs_url=None, redoc_url=None)

# ── helpers ────────────────────────────────────────────────────────────────


def _events_path() -> Path:
    return REPO_ROOT / "data" / "dashboard_events.ndjson"


def _reports_root() -> Path:
    return REPO_ROOT / "reports" / "research_os"


def _memory_dir() -> Path:
    return REPO_ROOT / "research_os_memory"


def _registries_dir() -> Path:
    return REPO_ROOT / "research_os_registries"


def _find_latest_result() -> Optional[Dict[str, Any]]:
    """Return the most recently modified result.json across all workflow runs."""
    best_path: Optional[Path] = None
    best_mtime = 0.0
    root = _reports_root()
    if not root.exists():
        return None
    for result_path in root.glob("*/*/result.json"):
        mtime = result_path.stat().st_mtime
        if mtime > best_mtime:
            best_mtime = mtime
            best_path = result_path
    if best_path is None:
        return None
    try:
        return json.loads(best_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _read_memory_headers() -> List[Dict[str, str]]:
    """Extract name/status/last_updated from each canonical markdown file header."""
    results = []
    mem_dir = _memory_dir()
    if not mem_dir.exists():
        return results
    for md_file in sorted(mem_dir.glob("*.md")):
        entry: Dict[str, str] = {"name": md_file.stem, "status": "unknown", "last_updated": "", "updated_by": ""}
        try:
            text = md_file.read_text(encoding="utf-8")
            for line in text.splitlines()[:10]:
                if m := re.match(r"^Last updated:\s*(.+)", line):
                    entry["last_updated"] = m.group(1).strip()
                elif m := re.match(r"^Updated by:\s*(.+)", line):
                    entry["updated_by"] = m.group(1).strip()
                elif m := re.match(r"^Status:\s*(.+)", line):
                    entry["status"] = m.group(1).strip()
        except Exception:
            pass
        results.append(entry)
    return results


def _read_registry_counts() -> Dict[str, int]:
    """Return entry counts for each JSON registry file."""
    counts: Dict[str, int] = {}
    reg_dir = _registries_dir()
    if not reg_dir.exists():
        return counts
    for jf in sorted(reg_dir.glob("*.json")):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
            counts[jf.stem] = len(data.get("entries", []))
        except Exception:
            counts[jf.stem] = -1
    return counts


# ── SSE endpoint ───────────────────────────────────────────────────────────

_KEEPALIVE = ": keepalive\n\n"
_POLL_INTERVAL = 0.5  # seconds


async def _tail_events(path: Path) -> AsyncIterator[str]:
    """Yield all existing NDJSON events then poll for new lines indefinitely."""
    yield _KEEPALIVE  # prevent browser timeout before first byte

    # Phase 1: replay history so late-joiners get full state
    offset = 0
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                for raw in f:
                    raw = raw.strip()
                    if raw:
                        yield f"data: {raw}\n\n"
            offset = path.stat().st_size
        except Exception:
            pass

    # Phase 2: tail new lines
    while True:
        await asyncio.sleep(_POLL_INTERVAL)
        if not path.exists():
            yield _KEEPALIVE
            continue
        try:
            current_size = path.stat().st_size
        except Exception:
            yield _KEEPALIVE
            continue
        if current_size <= offset:
            yield _KEEPALIVE
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                f.seek(offset)
                for raw in f:
                    raw = raw.strip()
                    if raw:
                        yield f"data: {raw}\n\n"
            offset = current_size
        except Exception:
            pass


@app.get("/events/stream")
async def events_stream() -> StreamingResponse:
    return StreamingResponse(
        _tail_events(_events_path()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── REST API ───────────────────────────────────────────────────────────────


@app.get("/api/state")
def get_state() -> Dict[str, Any]:
    """Current gate status, memory file headers, and registry counts."""
    latest = _find_latest_result()
    return {
        "gates": latest.get("gate_status", {}) if latest else {},
        "blocked": latest.get("blocked", False) if latest else False,
        "human_review_required": latest.get("human_review_required", False) if latest else False,
        "block_reason": latest.get("block_reason", "") if latest else "",
        "memory": _read_memory_headers(),
        "registries": _read_registry_counts(),
    }


@app.get("/api/runs")
def list_runs() -> List[Dict[str, Any]]:
    """List all workflow runs sorted newest-first."""
    root = _reports_root()
    if not root.exists():
        return []
    runs = []
    for result_path in root.glob("*/*/result.json"):
        workflow = result_path.parent.parent.name
        ts = result_path.parent.name
        try:
            data = json.loads(result_path.read_text(encoding="utf-8"))
            runs.append({
                "workflow": workflow,
                "ts": ts,
                "path": str(result_path),
                "blocked": data.get("blocked", False),
                "human_review_required": data.get("human_review_required", False),
                "agent_count": len(data.get("agent_outputs", [])),
                "mtime": result_path.stat().st_mtime,
            })
        except Exception:
            runs.append({"workflow": workflow, "ts": ts, "path": str(result_path),
                         "blocked": None, "mtime": result_path.stat().st_mtime})
    runs.sort(key=lambda r: r["mtime"], reverse=True)
    for r in runs:
        r.pop("mtime", None)
    return runs[:50]


@app.get("/api/run/{workflow}/{ts}")
def get_run(workflow: str, ts: str) -> Dict[str, Any]:
    """Return the full result.json for a specific run."""
    result_path = _reports_root() / workflow / ts / "result.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    try:
        return json.loads(result_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/run/{workflow}/{ts}/plan")
def get_run_plan(workflow: str, ts: str) -> Dict[str, Any]:
    """Return the plan.json for a specific run."""
    plan_path = _reports_root() / workflow / ts / "plan.json"
    if not plan_path.exists():
        raise HTTPException(status_code=404, detail="Plan not found")
    try:
        return json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/{filename}")
def get_memory_file(filename: str) -> Dict[str, str]:
    """Return the raw content of a canonical memory file."""
    safe = Path(filename).name  # strip any path traversal
    if not safe.endswith(".md"):
        safe += ".md"
    path = _memory_dir() / safe
    if not path.exists():
        raise HTTPException(status_code=404, detail="Memory file not found")
    return {"name": safe, "content": path.read_text(encoding="utf-8")}


# ── New endpoints (graph, transcripts, KB) ─────────────────────────────────


def _transcripts_root() -> Path:
    return REPO_ROOT / "reports" / "research_os" / "runs"


@app.get("/api/transcripts")
def list_transcripts() -> List[Dict[str, Any]]:
    """List all available per-run transcripts, newest first."""
    root = _transcripts_root()
    if not root.exists():
        return []
    out: List[Dict[str, Any]] = []
    for transcript in root.glob("*/*/transcript.jsonl"):
        workflow = transcript.parent.parent.name
        ts = transcript.parent.name
        try:
            mtime = transcript.stat().st_mtime
            size = transcript.stat().st_size
        except OSError:
            continue
        out.append({
            "workflow": workflow,
            "ts": ts,
            "path": str(transcript),
            "size": size,
            "mtime": mtime,
        })
    out.sort(key=lambda r: r["mtime"], reverse=True)
    for r in out:
        r.pop("mtime", None)
    return out[:50]


@app.get("/api/transcripts/{workflow}/{ts}")
def get_transcript(workflow: str, ts: str) -> Dict[str, Any]:
    """Return parsed events from a per-run transcript."""
    transcript = _transcripts_root() / workflow / ts / "transcript.jsonl"
    if not transcript.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    events: List[Dict[str, Any]] = []
    try:
        for line in transcript.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e))
    summary_text = ""
    summary_path = transcript.parent / "summary.md"
    if summary_path.exists():
        try:
            summary_text = summary_path.read_text(encoding="utf-8")
        except OSError:
            pass
    return {
        "workflow": workflow,
        "ts": ts,
        "events": events,
        "event_count": len(events),
        "summary_md": summary_text,
    }


def _parse_agent_registry_entries() -> List[Dict[str, Any]]:
    """Parse research_os_memory/AGENT_REGISTRY.md into a list of entries.

    We re-implement the same regex parser used by ``research_os.memory.registry_loader``
    so the dashboard module doesn't have to import the package (keeps the
    server boot independent of any package-level side effects).
    """
    md_path = _memory_dir() / "AGENT_REGISTRY.md"
    if not md_path.exists():
        return []
    out: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    for raw in md_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        m = re.match(r"^###\s+([a-z_][a-z0-9_]*)\s*$", line)
        if m:
            if current:
                out.append(current)
            current = {"agent_id": m.group(1)}
            continue
        if not current:
            continue
        fm = re.match(r"^\s*-\s+([a-z_]+)\s*:\s*(.*)$", line)
        if not fm:
            continue
        key, value = fm.group(1).lower(), fm.group(2).strip()
        if key in ("keywords", "required_gates", "related_agents", "workflows"):
            current[key] = [p.strip().strip('"\'') for p in value.split(",") if p.strip() and p.strip().lower() != "none"]
        elif key == "example_prompts":
            current[key] = re.findall(r'"([^"]+)"', value)
        else:
            current[key] = value
    if current:
        out.append(current)
    return out


@app.get("/api/agent-registry")
def get_agent_registry() -> Dict[str, Any]:
    """Return structured AGENT_REGISTRY.md entries for the graph view."""
    entries = _parse_agent_registry_entries()
    return {"count": len(entries), "agents": entries}


@app.get("/api/workflow-registry")
def get_workflow_registry() -> Dict[str, Any]:
    """Return the raw WORKFLOW_REGISTRY.md content plus a workflow name list."""
    md_path = _memory_dir() / "WORKFLOW_REGISTRY.md"
    text = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    names = re.findall(r"^##\s+([a-z_][a-z0-9_]*)\s*$", text, re.MULTILINE)
    return {"workflows": names, "content_md": text}


@app.get("/api/claims")
def get_claims() -> Dict[str, Any]:
    """Return parsed CURRENT_CLAIMS.md sections + the claim_registry."""
    md_path = _memory_dir() / "CURRENT_CLAIMS.md"
    md = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    registry_path = _registries_dir() / "claim_registry.json"
    claims: List[Dict[str, Any]] = []
    if registry_path.exists():
        try:
            data = json.loads(registry_path.read_text(encoding="utf-8"))
            claims = data.get("claims") or data.get("entries") or []
        except Exception:
            claims = []
    return {"current_claims_md": md, "claims": claims}


@app.get("/api/artifacts")
def get_artifacts() -> Dict[str, Any]:
    """Return the artifact_registry.json entries."""
    registry_path = _registries_dir() / "artifact_registry.json"
    if not registry_path.exists():
        return {"artifacts": []}
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception:
        return {"artifacts": []}
    return {"artifacts": data.get("artifacts") or data.get("entries") or []}


@app.get("/api/graph")
def get_graph() -> Dict[str, Any]:
    """Compose nodes + edges for the Obsidian-style graph view.

    Node types:
      - orchestrator (center)
      - agent (21 — from AGENT_REGISTRY.md)
      - memory (one per file in research_os_memory/)
      - registry (one per file in research_os_registries/)
      - gate (one per gate name)
      - workflow (one per workflow_registry entry)
    Edges connect orchestrator → agents and agents → their declared
    memory/registry/workflow links.
    """
    entries = _parse_agent_registry_entries()
    workflows = re.findall(
        r"^##\s+([a-z_][a-z0-9_]*)\s*$",
        ((_memory_dir() / "WORKFLOW_REGISTRY.md").read_text(encoding="utf-8") if (_memory_dir() / "WORKFLOW_REGISTRY.md").exists() else ""),
        re.MULTILINE,
    )
    memory_files = [p.stem for p in sorted(_memory_dir().glob("*.md"))] if _memory_dir().exists() else []
    registry_files = [p.stem for p in sorted(_registries_dir().glob("*.json"))] if _registries_dir().exists() else []
    gate_names = [
        "research_design", "dataset", "leakage", "preprocessing", "code",
        "evaluation", "validation", "claim", "figure", "submission",
    ]

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    nodes.append({
        "id": "master_orchestrator",
        "type": "orchestrator",
        "label": "Master Orchestrator",
        "radius": 36,
    })

    for entry in entries:
        agent_id = entry.get("agent_id")
        if not agent_id or agent_id == "master_orchestrator":
            continue
        nodes.append({
            "id": agent_id,
            "type": "agent",
            "label": entry.get("name", agent_id),
            "purpose": entry.get("purpose", ""),
            "risk_level": entry.get("risk_level", "medium"),
            "radius": 18,
        })
        edges.append({"source": "master_orchestrator", "target": agent_id, "kind": "selects"})
        for gate in entry.get("required_gates", []) or []:
            if gate and gate != "none" and gate in gate_names:
                edges.append({"source": agent_id, "target": f"gate:{gate}", "kind": "owns_gate"})
        for wf in entry.get("workflows", []) or []:
            wf_clean = wf.strip()
            if wf_clean and wf_clean in workflows:
                edges.append({"source": f"workflow:{wf_clean}", "target": agent_id, "kind": "includes"})

    for fname in memory_files:
        nodes.append({"id": f"memory:{fname}", "type": "memory", "label": fname, "radius": 11})
    for fname in registry_files:
        nodes.append({"id": f"registry:{fname}", "type": "registry", "label": fname, "radius": 11})
    for gate in gate_names:
        nodes.append({"id": f"gate:{gate}", "type": "gate", "label": gate, "radius": 13})
    for wf in workflows:
        nodes.append({"id": f"workflow:{wf}", "type": "workflow", "label": wf, "radius": 15})

    # Memory edges: AGENT_REGISTRY ↔ orchestrator + ROUTING_GUIDE ↔ orchestrator
    if "AGENT_REGISTRY" in memory_files:
        edges.append({"source": "master_orchestrator", "target": "memory:AGENT_REGISTRY", "kind": "reads"})
    if "ROUTING_GUIDE" in memory_files:
        edges.append({"source": "master_orchestrator", "target": "memory:ROUTING_GUIDE", "kind": "reads"})

    return {"nodes": nodes, "edges": edges}


# ── Static files (must be last) ────────────────────────────────────────────

_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
