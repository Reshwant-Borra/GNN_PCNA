"""Shared helper for extracting a JSON object from LLM output.

LLMs frequently wrap JSON in code fences, prefix with prose, or trail with
explanations. This helper handles those cases without depending on the
specific model. Used by both the semantic router (Ollama) and the Claude
fallback path so we don't have two parsers that drift.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Return the first balanced JSON object found in ``text``, or None.

    Strategy:
      1. Strip code fences (``` and ```json) from both ends.
      2. Try a direct ``json.loads``.
      3. Fall back to a greedy regex that captures the first {...} block.
    """
    if not text:
        return None
    cleaned = text.strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError:
        result = None
    if isinstance(result, dict):
        return result
    m = _JSON_BLOCK.search(cleaned)
    if not m:
        return None
    try:
        result = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return result if isinstance(result, dict) else None


__all__ = ["extract_json"]
