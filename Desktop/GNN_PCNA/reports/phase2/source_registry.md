# Source Registry

Date: 2026-05-27
Created by: Codex
Status: DRAFT

Machine-readable registry: `data/registries/source_registry.json`

## Rule

`crawls/` entries are source leads. They are not verified truth, not adopted datasets, and not claim support until individually checked against primary source metadata and governance.

## Registered Crawl Leads

| Source ID | Path | Total selected | Trust level | Adoption |
|---|---|---:|---|---|
| CRAWL-001 | `crawls/_adapter_probe/` | n/a | raw crawl lead | not adopted |
| CRAWL-002 | `crawls/_osf_probe/` | n/a | raw crawl lead | not adopted |
| CRAWL-003 | `crawls/_probe2/` | n/a | raw crawl lead | not adopted |
| CRAWL-004 | `crawls/gnn-compbio-autonomous-kb/` | n/a | raw crawl lead | not adopted |
| CRAWL-005 | `crawls/gnn-compbio-autonomous-kb-final/` | 220 | raw crawl lead | not adopted |
| CRAWL-006 | `crawls/pcna-biogrid-full-pass5/` | 1286 | raw crawl lead | not adopted |
| CRAWL-007 | `crawls/pcna-biogrid-interactions-pass4/` | 2 | raw crawl lead | not adopted |
| CRAWL-008 | `crawls/pcna-cryptic-pocket-gat-md-kb-1000/` | 774 | raw crawl lead | not adopted |
| CRAWL-009 | `crawls/pcna-cryptic-pocket-gat-md-kb-1000-pass2/` | 1500 | raw crawl lead | not adopted |
| CRAWL-010 | `crawls/pcna-cryptic-pocket-gat-md-kb-final/` | 4229 | raw crawl lead | not adopted |
| CRAWL-011 | `crawls/pcna-cryptic-pocket-gat-md-kb-tools-data-pass3/` | 8 | raw crawl lead | not adopted |
| CRAWL-012 | `crawls/pcna-curated-official-tools-data-structures-pass8/` | 177 | raw crawl lead | not adopted |
| CRAWL-013 | `crawls/pcna-dataset-repositories-pass9/` | 237 | raw crawl lead | not adopted |
| CRAWL-014 | `crawls/pcna-datasets-tools-repos-pass7/` | 51 | raw crawl lead | not adopted |
| CRAWL-015 | `crawls/pcna-gap-closure-datasets-tools-structures-pass6/` | 1399 | raw crawl lead | not adopted |

## Next Source Work

1. Verify CryptoBench source records and file access from `crawls/pcna-dataset-repositories-pass9/`.
2. Verify curated official database/tool leads from `crawls/pcna-curated-official-tools-data-structures-pass8/`.
3. Verify PCNA/AOH1996/8GLA source records from `crawls/pcna-cryptic-pocket-gat-md-kb-final/` and raw PDB/UniProt probe paths.

## Governance

- `docs/scientific_governance/01_SOURCE_OF_TRUTH.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`

## Conclusion

Source registry scaffolding exists. No source is adopted for training, evaluation, MD, or claims.
