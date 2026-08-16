"""Allosteric Database official-link intake adapter."""

from __future__ import annotations

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


class AsdAdapter(SourceAdapter):
    source_name = "asd"
    intended_role = "allosteric context source"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        return [
            DownloadCandidate(
                source_name=self.source_name,
                target="asd_official_home",
                url="https://mdl.shsmu.edu.cn/ASD/",
                official_url="https://mdl.shsmu.edu.cn/ASD/",
                intended_role=self.intended_role,
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_UNKNOWN",
                trust_level="official_metadata",
                link_only=True,
                download=False,
                expected_file_type="html",
                contains_metadata=True,
                pcna_screening_status="simple_text_screen_possible",
                homolog_screening_status="requires_sequence_parse",
                notes="Official ASD page linked only. Allosteric context is not automatically residue-level training data.",
            )
        ]

