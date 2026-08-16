"""Baseline contracts without executing external tools or making claims."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaselineRunSpec:
    name: str
    input_policy: str = "same frozen split and same label definition required"
    provenance_required: bool = True
    status: str = "WRAPPER_ONLY_NOT_EXECUTED"

