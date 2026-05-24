"""
Natural-language → Orchestrator intent parser.

Takes a free-form Telegram message ("train for 50 epochs", "bundle the repo",
"how many pending tasks?") and resolves it to one of the registered intents
in agents/orchestrator.py, with structured args.

Backend: Gemma 3:4b via Ollama (same pattern as agents/local_agent.py +
agents/gemma_verifier.py). No API cost, no key, runs on the same box as the
gateway. The LLM ONLY classifies — it never executes anything. The orchestrator
still applies role gates + approval queue, so a wrong classification can't
bypass safety; the worst case is the user has to /deny the resulting task.

Output schema (strict JSON):
    {"intent": "<name>", "args": {...}}             — resolved
    {"clarify": "<question>"}                       — ambiguous
    {"error": "<reason>"}                           — unrecognised / unsafe

Usage:
    from agents.intent_parser import parse
    result = parse("train for 50 epochs")
    # → {"intent": "train", "args": {"epochs": 50}}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agents.orchestrator import INTENTS  # noqa: E402

MODEL    = "gemma3:4b"
ENDPOINT = "http://localhost:11434/api/chat"


def _health_check() -> bool:
    import urllib.request, time
    for url in ("http://localhost:11434", "http://127.0.0.1:11434"):
        for _ in range(3):
            try:
                urllib.request.urlopen(url, timeout=3)
                return True
            except Exception:
                time.sleep(1)
    return False


def _intent_catalog() -> str:
    """Render the live intent registry as a numbered catalog for the prompt."""
    lines = []
    for name, spec in INTENTS.items():
        tags = []
        if spec.risky:        tags.append("RISKY")
        if spec.long_running: tags.append("LONG")
        tag = f" [{'/'.join(tags)}]" if tags else ""
        lines.append(f"- {name}{tag}: {spec.description}")
    return "\n".join(lines)


_SYSTEM = """\
You are the intent classifier for ResearchOS, a GNN-PCNA research pipeline
running on an RTX 4070 GPU machine. The repo is at ~/GNN_PCNA.
You receive a natural-language message from an approved owner and must
map it to exactly ONE registered intent, with structured args.

You DO NOT execute anything. You only emit JSON.

Rules:
- Output ONLY valid JSON. No prose, no markdown, no code fences.
- If the message clearly maps to a specific intent, emit:
    {"intent": "<exact_name_from_catalog>", "args": {<key>: <value>, ...}}
- If the message describes any compute task not covered by a specific intent
  (e.g. MD simulation, custom script, file generation, GPU benchmark, anything
  arbitrary), use the "shell" intent and generate the appropriate bash command:
    {"intent": "shell", "args": {"cmd": "<full bash command string>"}}
  The machine has: python3, torch, openmm, cuda, gromacs, git, standard GNU tools.
  Repo root is ~/GNN_PCNA. Output large files to ~/GNN_PCNA/data/artifacts/.
- If the message is ambiguous, emit:
    {"clarify": "<single short question>"}
- Args for specific intents (only if mentioned):
    epochs (int), batch_size (int), lr (float), patience (int),
    cutoff (float), workers (int), limit (int),
    model_size ("small"|"medium"|"large"),
    cuda (bool), build (bool), pdb_id (str),
    from_stage (str), only (list[str]), skip (list[str])
- Never combine intents.
"""

_USER_TEMPLATE = """\
Available intents:
{catalog}

Live repo context:
{repo_context}

User message:
{message}

Emit the JSON now.
"""


def _run(cmd: str) -> str:
    """Run a shell command, return stdout, never raise."""
    try:
        import subprocess as _sp
        return _sp.check_output(cmd, shell=True, cwd=str(REPO_ROOT),
                                stderr=_sp.DEVNULL, timeout=10,
                                encoding="utf-8", errors="replace").strip()
    except Exception:
        return ""


def _gather_repo_context() -> str:
    """Read live repo structure, all branches, and environment so Gemma has full context."""
    context = ""

    # --- current branch + all branches + files on each ---
    current_branch = _run("git rev-parse --abbrev-ref HEAD")
    all_branches = _run("git branch -a --format=%(refname:short)").splitlines()
    context += f"=== current branch ===\n{current_branch}\n"
    context += f"\n=== all branches ===\n" + "\n".join(all_branches)

    # Files on every branch (ls-tree)
    seen = set()
    branch_files: list[str] = []
    for branch in all_branches:
        branch = branch.strip().lstrip("* ")
        if branch.startswith("origin/HEAD"):
            continue
        files = _run(f"git ls-tree -r --name-only {branch}")
        for f in files.splitlines():
            if f not in seen:
                seen.add(f)
                branch_files.append(f"[{branch}] {f}")
    context += "\n\n=== all files across all branches ===\n" + "\n".join(branch_files[:300])

    # --- checked-out tree (2 levels) ---
    lines = []
    skip = {".git", "__pycache__", ".obsidian", "node_modules", ".venv", "venv"}
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in sorted(dirs) if d not in skip]
        depth = len(Path(root).relative_to(REPO_ROOT).parts)
        if depth > 2:
            continue
        indent = "  " * depth
        label = Path(root).name if depth > 0 else "."
        lines.append(f"{indent}{label}/")
        for f in sorted(files):
            lines.append(f"{indent}  {f}")
    context += "\n\n=== checked-out tree ===\n" + "\n".join(lines[:150])

    # --- key reference files ---
    for fname in ["REPO_MAP.md", "AGENTS.md", "CLAUDE.md", "README.md"]:
        p = REPO_ROOT / fname
        if p.exists():
            content = p.read_text(encoding="utf-8", errors="replace")[:2000]
            context += f"\n\n=== {fname} ===\n{content}"

    # --- data / checkpoints / scripts / src file listing ---
    for folder in ["data", "checkpoints", "scripts", "src"]:
        p = REPO_ROOT / folder
        if p.exists():
            entries = sorted(str(x.relative_to(REPO_ROOT))
                             for x in p.rglob("*") if x.is_file())[:40]
            context += f"\n\n=== {folder}/ ===\n" + "\n".join(entries)

    # --- Python / conda environment ---
    context += "\n\n=== python env ==="
    context += "\n" + _run("which python || which python3")
    context += "\n" + _run("python --version 2>&1 || python3 --version 2>&1")
    context += "\n" + _run("conda info --envs 2>/dev/null || echo 'no conda'")
    context += "\n" + _run("pip list 2>/dev/null | grep -iE 'torch|openmm|cuda|numpy|scipy|sklearn' || true")

    # --- CUDA / GPU ---
    context += "\n\n=== gpu ==="
    context += "\n" + _run("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || echo 'no nvidia-smi'")
    context += "\n" + _run("python -c \"import torch; print('torch', torch.__version__, 'cuda:', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')\" 2>/dev/null || echo 'torch not available'")

    return context


def parse(message: str, timeout_s: float = 15.0) -> dict[str, Any]:
    """
    Classify a free-form message into an orchestrator intent.

    Returns one of:
        {"intent": str, "args": dict}
        {"clarify": str}
        {"error": str}
    """
    message = (message or "").strip()
    if not message:
        return {"error": "empty message"}

    prompt = _USER_TEMPLATE.format(
        catalog=_intent_catalog(),
        repo_context=_gather_repo_context(),
        message=message,
    )
    try:
        import urllib.request, json as _json
        payload = _json.dumps({
            "model": MODEL,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user",   "content": prompt},
            ],
            "stream": False,
            "options": {"temperature": 0},
        }).encode()
        req = urllib.request.Request(ENDPOINT, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = _json.loads(resp.read())["message"]["content"]
    except Exception as e:
        return {"error": f"llm call failed: {str(e)[:120]}"}

    parsed = _extract_json(raw)
    if parsed is None:
        return {"error": f"parser returned non-JSON: {raw[:120]}"}

    return _validate(parsed)


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> dict[str, Any] | None:
    """Pull the first balanced JSON object out of model output."""
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_BLOCK.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


_ALLOWED_ARG_KEYS = {
    "epochs", "batch_size", "lr", "patience",
    "cutoff", "workers", "limit",
    "model_size", "cuda", "build",
    "pdb_id",
    "from_stage", "only", "skip",
    "checkpoint", "sources",
    "cmd",
}


def _validate(parsed: dict[str, Any]) -> dict[str, Any]:
    if "intent" in parsed:
        name = parsed.get("intent")
        if not isinstance(name, str) or name not in INTENTS:
            return {"error": f"unknown intent: {name!r}"}
        raw_args = parsed.get("args") or {}
        if not isinstance(raw_args, dict):
            return {"error": "args must be an object"}
        args = {k: v for k, v in raw_args.items() if k in _ALLOWED_ARG_KEYS}
        return {"intent": name, "args": args}
    if "clarify" in parsed:
        return {"clarify": str(parsed["clarify"])[:280]}
    if "error" in parsed:
        return {"error": str(parsed["error"])[:280]}
    return {"error": "parser output missing intent/clarify/error"}


# ── CLI for local testing ────────────────────────────────────────────────────

def _main() -> None:
    p = argparse.ArgumentParser(description="Intent parser CLI (debug)")
    p.add_argument("message", nargs="+", help="Free-form message to classify")
    args = p.parse_args()
    result = parse(" ".join(args.message))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    _main()
