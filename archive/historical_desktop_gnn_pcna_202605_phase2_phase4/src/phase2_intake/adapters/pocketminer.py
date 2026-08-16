"""PocketMiner baseline/method reference intake adapter."""

from __future__ import annotations

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


class PocketMinerAdapter(SourceAdapter):
    source_name = "pocketminer"
    intended_role = "baseline and method reference"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        return [
            DownloadCandidate(
                source_name=self.source_name,
                target="pocketminer_paper_doi",
                url="https://doi.org/10.1038/s41467-023-36699-3",
                official_url="https://doi.org/10.1038/s41467-023-36699-3",
                intended_role=self.intended_role,
                license_status="TERMS_UNKNOWN",
                schema_status="SCHEMA_UNKNOWN",
                trust_level="official_metadata",
                link_only=True,
                download=False,
                expected_file_type="html",
                contains_metadata=True,
                notes="Paper DOI linked only; do not store full text unless terms allow it.",
            ),
            DownloadCandidate(
                source_name=self.source_name,
                target="pocketminer_github_metadata",
                url="https://api.github.com/repos/Mickdub/gvp",
                official_url="https://github.com/Mickdub/gvp",
                relative_path="metadata/github_repo_Mickdub_gvp.json",
                intended_role="PocketMiner-related code metadata",
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_PARTIAL",
                trust_level="official_metadata",
                expected_file_type="json",
                contains_metadata=True,
                contains_code=True,
                notes="Repository metadata only; runnable baseline status remains unverified.",
            ),
        ]

