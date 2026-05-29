"""BioGRID and STRING targeted metadata adapters."""

from __future__ import annotations

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


class BioGridStringAdapter(SourceAdapter):
    source_name = "biogrid"
    intended_role = "targeted PCNA interaction context"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        return [
            DownloadCandidate(
                source_name="biogrid",
                target="biogrid_official_home",
                url="https://thebiogrid.org/",
                official_url="https://thebiogrid.org/",
                intended_role="PCNA interaction context",
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_UNKNOWN",
                trust_level="official_metadata",
                link_only=True,
                download=False,
                expected_file_type="html",
                contains_metadata=True,
                notes="Official BioGRID homepage linked only pending API/license review.",
            ),
            DownloadCandidate(
                source_name="string",
                target="string_pcna_uniprot_p12004",
                url="https://string-db.org/network/9606.ENSP00000368411",
                official_url="https://string-db.org/",
                intended_role="PCNA functional association context",
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_UNKNOWN",
                trust_level="official_metadata",
                link_only=True,
                download=False,
                expected_file_type="html",
                contains_metadata=True,
                notes="STRING link only; do not bulk-download STRING files during intake.",
            ),
        ]

