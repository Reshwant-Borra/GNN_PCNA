"""PubMed literature metadata adapter."""

from __future__ import annotations

from urllib.parse import quote

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


DEFAULT_QUERIES = [
    "CryptoBench cryptic protein ligand binding sites",
    "PCNA AOH1996 8GLA",
    "PocketMiner cryptic pockets",
]


class PubMedAdapter(SourceAdapter):
    source_name = "literature_metadata"
    intended_role = "literature metadata only"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        queries = context.targets or DEFAULT_QUERIES
        candidates: list[DownloadCandidate] = []
        for index, query in enumerate(queries, start=1):
            encoded = quote(query)
            candidates.append(
                DownloadCandidate(
                    source_name=self.source_name,
                    target=f"pubmed_query_{index}",
                    url=f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=20&term={encoded}",
                    official_url="https://pubmed.ncbi.nlm.nih.gov/",
                    relative_path=f"pubmed/query_{index}.json",
                    intended_role=self.intended_role,
                    license_status="LICENSE_KNOWN",
                    schema_status="SCHEMA_PARTIAL",
                    trust_level="official_metadata",
                    expected_file_type="json",
                    contains_metadata=True,
                    notes=f"PubMed metadata query only: {query}",
                )
            )
        return candidates

