"""fpocket and P2Rank baseline tool metadata adapter."""

from __future__ import annotations

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.models import DownloadCandidate


class BaselineToolsAdapter(SourceAdapter):
    source_name = "baseline_tools"
    intended_role = "baseline tool metadata and documentation"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        return [
            DownloadCandidate(
                source_name=self.source_name,
                target="fpocket_github_metadata",
                url="https://api.github.com/repos/Discngine/fpocket",
                official_url="https://github.com/Discngine/fpocket",
                relative_path="fpocket/metadata/github_repo_Discngine_fpocket.json",
                intended_role="fpocket baseline tool metadata",
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_PARTIAL",
                trust_level="official_metadata",
                expected_file_type="json",
                contains_code=True,
                contains_metadata=True,
                notes="Tool metadata only; installation and output schema remain unverified.",
            ),
            DownloadCandidate(
                source_name=self.source_name,
                target="p2rank_github_metadata",
                url="https://api.github.com/repos/rdk/p2rank",
                official_url="https://github.com/rdk/p2rank",
                relative_path="p2rank/metadata/github_repo_rdk_p2rank.json",
                intended_role="P2Rank baseline tool metadata",
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_PARTIAL",
                trust_level="official_metadata",
                expected_file_type="json",
                contains_code=True,
                contains_metadata=True,
                notes="Tool metadata only; installation and residue-score extraction remain unverified.",
            ),
        ]

