"""RCSB PDB targeted intake adapter for PCNA-related structures."""

from __future__ import annotations

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


DEFAULT_PCNA_PDB_TARGETS = ["8GLA", "1W60"]


class RcsbPdbAdapter(SourceAdapter):
    source_name = "pcna_structures"
    intended_role = "targeted PCNA experimental structure source"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        targets = [target.upper() for target in context.targets] or DEFAULT_PCNA_PDB_TARGETS
        candidates: list[DownloadCandidate] = []
        for pdb_id in targets:
            candidates.extend(
                [
                    DownloadCandidate(
                        source_name=self.source_name,
                        target=f"{pdb_id}_metadata",
                        url=f"https://data.rcsb.org/rest/v1/core/entry/{pdb_id}",
                        official_url=f"https://www.rcsb.org/structure/{pdb_id}",
                        relative_path=f"{pdb_id}/metadata/{pdb_id}_entry.json",
                        intended_role=self.intended_role,
                        license_status="LICENSE_KNOWN",
                        schema_status="SCHEMA_PARTIAL",
                        trust_level="official_metadata",
                        expected_file_type="json",
                        contains_metadata=True,
                        pcna_screening_status="requires_schema_parse",
                        homolog_screening_status="requires_sequence_parse",
                        notes="RCSB entry metadata. Apo/holo and biological-assembly use remain unverified.",
                    ),
                    DownloadCandidate(
                        source_name=self.source_name,
                        target=f"{pdb_id}_mmcif",
                        url=f"https://files.rcsb.org/download/{pdb_id}.cif",
                        official_url=f"https://www.rcsb.org/structure/{pdb_id}",
                        relative_path=f"{pdb_id}/structures/{pdb_id}.cif",
                        intended_role=self.intended_role,
                        license_status="LICENSE_KNOWN",
                        schema_status="SCHEMA_PARTIAL",
                        trust_level="official",
                        expected_file_type="mmcif",
                        contains_structures=True,
                        contains_metadata=True,
                        pcna_screening_status="requires_structure_parse",
                        homolog_screening_status="requires_sequence_parse",
                        notes="Canonical RCSB mmCIF coordinate file. No graph or biological claim is authorized.",
                    ),
                ]
            )
        return candidates


class RcsbGenericAdapter(RcsbPdbAdapter):
    source_name = "rcsb_pdb"
    intended_role = "targeted RCSB PDB structure source"

