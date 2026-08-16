"""scPDB official-link intake adapter."""

from __future__ import annotations

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


class ScPdbAdapter(SourceAdapter):
    source_name = "scpdb"
    intended_role = "auxiliary binding-pocket/proxy source"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        return [
            DownloadCandidate(
                source_name=self.source_name,
                target="scpdb_official_home",
                url="http://bioinfo-pharma.u-strasbg.fr/scPDB/",
                official_url="http://bioinfo-pharma.u-strasbg.fr/scPDB/",
                intended_role=self.intended_role,
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_UNKNOWN",
                trust_level="official_metadata",
                link_only=True,
                download=False,
                expected_file_type="html",
                contains_metadata=True,
                pcna_screening_status="requires_schema_parse",
                homolog_screening_status="requires_sequence_parse",
                notes="Official scPDB page linked only pending terms and bulk-size approval.",
            )
        ]

