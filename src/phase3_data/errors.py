"""Fail-closed exceptions for governed Phase 3 data preparation."""

from __future__ import annotations


class Phase3DataError(RuntimeError):
    """Raised when a governed Phase 3 data precondition is not satisfied."""

