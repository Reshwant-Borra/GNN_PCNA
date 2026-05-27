"""CryptoBench official-source intake adapter."""

from __future__ import annotations

import json
from pathlib import Path

from phase2_intake.adapters.base import AdapterContext, SourceAdapter
from phase2_intake.config import ROOT
from phase2_intake.models import DownloadCandidate


CRYPTOBENCH_LOCAL_ROOT = ROOT / "data" / "raw_intake" / "cryptobench"


def _safe_name(name: str) -> str:
    keep = []
    for char in name:
        if char.isalnum() or char in {".", "-", "_"}:
            keep.append(char)
        else:
            keep.append("_")
    return "".join(keep).strip("._") or "unnamed"


def _load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _license_status_from_local_node() -> str:
    license_data = _load_json(CRYPTOBENCH_LOCAL_ROOT / "metadata" / "osf_license_563c1cf88c5e4a3877f9e972.json")
    if license_data:
        license_name = license_data.get("data", {}).get("attributes", {}).get("name")
        if license_name:
            return "LICENSE_KNOWN"
    return "LICENSE_UNRESOLVED"


def _file_contains_flags(name: str) -> dict[str, bool]:
    lower = name.lower()
    return {
        "contains_structures": any(token in lower for token in [".cif", ".mmcif", ".pdb", "structure", "structures"]),
        "contains_labels": any(token in lower for token in ["label", "labels", "pocket", "site", "sites"]),
        "contains_splits": any(token in lower for token in ["split", "train", "test", "validation", "val"]),
        "contains_metadata": any(token in lower for token in [".json", ".csv", ".tsv", ".txt", ".md", "readme", "metadata"]),
        "contains_code": any(token in lower for token in [".py", ".ipynb", "script", "code"]),
    }


class CryptoBenchAdapter(SourceAdapter):
    source_name = "cryptobench"
    intended_role = "primary cryptic-pocket benchmark candidate"

    def candidates(self, context: AdapterContext) -> list[DownloadCandidate]:
        candidates = [
            DownloadCandidate(
                source_name=self.source_name,
                target="osf_project_pz4a9_metadata",
                url="https://api.osf.io/v2/nodes/pz4a9/",
                official_url="https://osf.io/pz4a9/",
                relative_path="metadata/osf_node_pz4a9.json",
                intended_role=self.intended_role,
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_PARTIAL",
                trust_level="official_metadata",
                expected_file_type="json",
                contains_metadata=True,
                pcna_screening_status="simple_text_screen_possible",
                homolog_screening_status="requires_sequence_parse",
                notes="Official OSF API metadata for CryptoBench project. Dataset files remain untrusted until separately inventoried.",
            ),
            DownloadCandidate(
                source_name=self.source_name,
                target="osf_project_pz4a9_file_listing",
                url="https://api.osf.io/v2/nodes/pz4a9/files/",
                official_url="https://osf.io/pz4a9/files/osfstorage",
                relative_path="metadata/osf_node_pz4a9_files.json",
                intended_role=self.intended_role,
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_PARTIAL",
                trust_level="official_metadata",
                expected_file_type="json",
                contains_metadata=True,
                pcna_screening_status="requires_schema_parse",
                homolog_screening_status="requires_sequence_parse",
                notes="Official OSF file listing endpoint. Individual data files require size/license checks before download.",
            ),
            DownloadCandidate(
                source_name=self.source_name,
                target="osf_project_pz4a9_license",
                url="https://api.osf.io/v2/licenses/563c1cf88c5e4a3877f9e972/",
                official_url="https://osf.io/pz4a9/",
                relative_path="metadata/osf_license_563c1cf88c5e4a3877f9e972.json",
                intended_role="official CryptoBench license metadata",
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_PARTIAL",
                trust_level="official_metadata",
                expected_file_type="json",
                contains_metadata=True,
                notes="Official OSF license record. Human review is still required before dataset adoption.",
            ),
            DownloadCandidate(
                source_name=self.source_name,
                target="osf_project_pz4a9_osfstorage_root",
                url="https://api.osf.io/v2/nodes/pz4a9/files/osfstorage/",
                official_url="https://osf.io/pz4a9/files/osfstorage",
                relative_path="metadata/osf_node_pz4a9_osfstorage_root.json",
                intended_role="official CryptoBench OSF storage root listing",
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_PARTIAL",
                trust_level="official_metadata",
                expected_file_type="json",
                contains_metadata=True,
                pcna_screening_status="requires_schema_parse",
                homolog_screening_status="requires_sequence_parse",
                notes="Official OSF storage root listing. Data files discovered from it remain untrusted and gated.",
            ),
            DownloadCandidate(
                source_name=self.source_name,
                target="cryptobench_github_repo",
                url="https://api.github.com/repos/skrhakv/CryptoBench",
                official_url="https://github.com/skrhakv/CryptoBench",
                relative_path="metadata/github_repo_skrhakv_CryptoBench.json",
                intended_role="official code/tutorial metadata for CryptoBench",
                license_status="LICENSE_UNRESOLVED",
                schema_status="SCHEMA_PARTIAL",
                trust_level="official_metadata",
                expected_file_type="json",
                contains_metadata=True,
                contains_code=True,
                pcna_screening_status="simple_text_screen_possible",
                homolog_screening_status="requires_sequence_parse",
                notes="GitHub repository metadata only; code assets are not adopted as data.",
            ),
            DownloadCandidate(
                source_name=self.source_name,
                target="cryptobench_paper_doi",
                url="https://doi.org/10.1093/bioinformatics/btae745",
                official_url="https://doi.org/10.1093/bioinformatics/btae745",
                intended_role="paper metadata and benchmark context",
                license_status="TERMS_UNKNOWN",
                schema_status="SCHEMA_UNKNOWN",
                trust_level="official_metadata",
                link_only=True,
                download=False,
                expected_file_type="html",
                contains_metadata=True,
                notes="Linked only to avoid storing article text unless terms are reviewed.",
            ),
        ]
        candidates.extend(self._candidates_from_local_osf_listings())
        return candidates

    def _candidates_from_local_osf_listings(self) -> list[DownloadCandidate]:
        license_status = _license_status_from_local_node()
        candidates: list[DownloadCandidate] = []
        listing_paths = sorted((CRYPTOBENCH_LOCAL_ROOT / "metadata").glob("osf_listing_*.json"))
        root_listing = CRYPTOBENCH_LOCAL_ROOT / "metadata" / "osf_node_pz4a9_osfstorage_root.json"
        if root_listing.is_file():
            listing_paths.insert(0, root_listing)

        seen_urls: set[str] = set()
        for listing_path in listing_paths:
            data = _load_json(listing_path)
            if not data:
                continue
            for item in data.get("data", []):
                attributes = item.get("attributes", {})
                relationships = item.get("relationships", {})
                links = item.get("links", {})
                name = attributes.get("name") or item.get("id", "unnamed")
                kind = attributes.get("kind")
                item_id = item.get("id", "")
                safe = _safe_name(f"{item_id}_{name}")
                if kind == "folder":
                    href = relationships.get("files", {}).get("links", {}).get("related", {}).get("href")
                    if href and href not in seen_urls:
                        seen_urls.add(href)
                        candidates.append(
                            DownloadCandidate(
                                source_name=self.source_name,
                                target=f"osf_folder_listing_{safe}",
                                url=href,
                                official_url="https://osf.io/pz4a9/files/osfstorage",
                                relative_path=f"metadata/osf_listing_{safe}.json",
                                intended_role="official CryptoBench nested OSF folder listing",
                                license_status="LICENSE_UNRESOLVED",
                                schema_status="SCHEMA_PARTIAL",
                                trust_level="official_metadata",
                                expected_file_type="json",
                                contains_metadata=True,
                                pcna_screening_status="requires_schema_parse",
                                homolog_screening_status="requires_sequence_parse",
                                notes=f"Nested OSF folder listing for {name}.",
                            )
                        )
                    continue

                download_url = links.get("download")
                if not download_url:
                    continue
                flags = _file_contains_flags(name)
                target_dir = "files"
                if flags["contains_structures"]:
                    target_dir = "structures"
                elif flags["contains_labels"] or flags["contains_splits"]:
                    target_dir = "labels_or_splits"
                elif flags["contains_code"]:
                    target_dir = "code"
                elif flags["contains_metadata"]:
                    target_dir = "metadata_files"

                candidates.append(
                    DownloadCandidate(
                        source_name=self.source_name,
                        target=f"osf_file_{safe}",
                        url=download_url,
                        official_url=links.get("html") or "https://osf.io/pz4a9/files/osfstorage",
                        relative_path=f"{target_dir}/{safe}",
                        intended_role=self.intended_role,
                        license_status=license_status,
                        schema_status="SCHEMA_UNKNOWN",
                        trust_level="official",
                        expected_file_type=Path(name).suffix.lower().lstrip(".") or "unknown",
                        contains_structures=flags["contains_structures"],
                        contains_labels=flags["contains_labels"],
                        contains_splits=flags["contains_splits"],
                        contains_metadata=flags["contains_metadata"],
                        contains_code=flags["contains_code"],
                        pcna_screening_status="requires_schema_parse",
                        homolog_screening_status="requires_sequence_parse",
                        notes=f"Official OSF file discovered from listing: {name}. Download remains gated by license and size.",
                    )
                )
        return candidates
