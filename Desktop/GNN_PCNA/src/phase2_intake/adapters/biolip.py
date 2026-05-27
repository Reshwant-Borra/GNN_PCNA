"""BioLiP/BioLiP2/Q-BioLiP official-link intake adapter."""

from __future__ import annotations

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


class BioLipAdapter(SourceAdapter):
    source_name = "biolip"
    intended_role = "auxiliary ligand-contact/proxy label source"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        return [
            DownloadCandidate(
                source_name=self.source_name,
                target="biolip_official_home",
                url="https://zhanggroup.org/BioLiP/",
                official_url="https://zhanggroup.org/BioLiP/",
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
                notes="Official BioLiP page linked only pending terms and download-size review.",
            ),
            DownloadCandidate(
                source_name=self.source_name,
                target="q_biolip_official_home",
                url="https://zhanggroup.org/BioLiP/qbiolip/",
                official_url="https://zhanggroup.org/BioLiP/qbiolip/",
                intended_role="auxiliary curated ligand-contact context",
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_UNKNOWN",
                trust_level="official_metadata",
                link_only=True,
                download=False,
                expected_file_type="html",
                contains_metadata=True,
                notes="Q-BioLiP linked only. Labels are ligand-contact/proxy labels, not cryptic-pocket truth.",
            ),
        ]

