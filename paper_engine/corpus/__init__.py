"""Literature corpus subsystem: legal open-access discovery, download, extract, index.

Scale is reached through *legal* open-access bulk sources (OpenAlex, Europe PMC,
arXiv, Unpaywall, PMC OA), filtered to the project's domain. This module never
bypasses paywalls or violates publisher terms: it downloads only files an
open-access location explicitly exposes, rate-limits per host, and records
provenance for every item.
"""

__all__ = ["bulk_sources", "download_manager", "extract", "index"]
