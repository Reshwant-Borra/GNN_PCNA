"""Targeted AlphaFold DB adapter."""

from __future__ import annotations

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


DEFAULT_UNIPROT_TARGETS = ["P12004"]


class AlphaFoldAdapter(SourceAdapter):
    source_name = "alphafold"
    intended_role = "targeted predicted-structure context only"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        targets = [target.upper() for target in context.targets] or DEFAULT_UNIPROT_TARGETS
        candidates: list[DownloadCandidate] = []
        for uniprot_id in targets:
            candidates.append(
                DownloadCandidate(
                    source_name=self.source_name,
                    target=f"{uniprot_id}_alphafold_metadata",
                    url=f"https://alphafold.ebi.ac.uk/api/prediction/{uniprot_id}",
                    official_url=f"https://alphafold.ebi.ac.uk/entry/{uniprot_id}",
                    relative_path=f"{uniprot_id}/metadata/alphafold_{uniprot_id}.json",
                    intended_role=self.intended_role,
                    license_status="LICENSE_UNRESOLVED",
                    schema_status="SCHEMA_PARTIAL",
                    trust_level="official_metadata",
                    expected_file_type="json",
                    contains_metadata=True,
                    contains_structures=False,
                    pcna_screening_status="requires_schema_parse",
                    homolog_screening_status="requires_sequence_parse",
                    notes="Targeted AlphaFold metadata only by default; predicted structures are not labels.",
                )
            )
        return candidates

