"""Config-aware local LLM calls (Ollama).

``research_os.agents.base.call_ollama`` hardcodes the audit model; the paper
writer needs the configurable ``config.WRITER_MODEL`` plus longer outputs and
explicit CPU-thread options. This module provides that without adding
dependencies (uses urllib like the base helper).
"""
from __future__ import annotations

import json
import urllib.request
from typing import Optional

from paper_engine import config


def generate(
    prompt: str,
    *,
    system: str = "",
    model: Optional[str] = None,
    temperature: float = 0.4,
    num_predict: int = 800,
    num_ctx: int = 4096,
    timeout: int = 900,
) -> Optional[str]:
    """Generate text from the local model. Returns None on any error."""
    model = model or config.WRITER_MODEL
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    options = {
        "temperature": temperature,
        "num_predict": num_predict,
        "num_ctx": num_ctx,
    }
    # Only pin threads if explicitly overridden; otherwise let Ollama optimize.
    if config.OLLAMA_NUM_THREAD:
        options["num_thread"] = config.OLLAMA_NUM_THREAD
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": options,
    }).encode()
    endpoint = f"{config.OLLAMA_HOST.rstrip('/')}/api/chat"
    try:
        req = urllib.request.Request(
            endpoint, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["message"]["content"]
    except Exception:
        return None


def available(model: Optional[str] = None) -> bool:
    """Cheap reachability check for the configured model."""
    return generate("Reply with: OK", system="You are terse.",
                    num_predict=5, timeout=30) is not None


def warm(model: Optional[str] = None) -> bool:
    """Pre-load the model so the first real call doesn't pay cold-start latency.

    Returns True if the model responded. Uses a generous timeout because the
    first load of a multi-GB model on CPU can take a while.
    """
    return generate("ok", system="Reply with one word.",
                    model=model, num_predict=2, num_ctx=512, timeout=240) is not None
