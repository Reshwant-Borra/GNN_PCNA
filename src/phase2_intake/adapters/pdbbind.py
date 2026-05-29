"""PDBbind official-link intake adapter."""

from __future__ import annotations

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


class PdbBindAdapter(SourceAdapter):
    source_name = "pdbbind"
    intended_role = "auxiliary protein-ligand affinity context only"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        return [
            DownloadCandidate(
                source_name=self.source_name,
                target="pdbbind_official_home",
                url="http://www.pdbbind.org.cn/",
                official_url="http://www.pdbbind.org.cn/",
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
                notes="PDBbind is affinity/protein-ligand context, not primary cryptic-pocket ground truth. Linked only pending access and terms.",
            )
        ]

