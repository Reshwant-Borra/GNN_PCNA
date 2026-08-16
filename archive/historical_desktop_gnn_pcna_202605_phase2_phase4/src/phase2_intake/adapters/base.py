"""Source adapter interfaces and helper adapters."""

from __future__ import annotations

from dataclasses import dataclass

from phase2_intake.models import DownloadCandidate


@dataclass(frozen=True)
class AdapterContext:
    targets: list[str]


class SourceAdapter:
    source_name = "base"
    intended_role = "source acquisition"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        raise NotImplementedError

