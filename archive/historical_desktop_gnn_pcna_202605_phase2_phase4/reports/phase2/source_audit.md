# Source Audit

Date: 2026-05-27
Created by: Codex
Status: DRAFT

## Checks

| Check | Result | Notes |
|---|---|---|
| Crawl directories enumerated | PASS | See `data/registries/source_registry.json`. |
| SOURCE_INDEX hashes recorded where available | PASS | Hashes recorded for selected high-priority crawl leads. |
| Crawls treated as leads only | PASS | All registry entries have `adoption_status: not_adopted`. |
| Raw availability checked at bundle level | PASS WITH WARNING | `pcna-cryptic-pocket-gat-md-kb-final` lacks a direct `raw/` directory. |
| Primary evidence verified | FAIL | Not performed in this milestone. |
| Dataset adoption | FAIL | No dataset is adopted. |

## Blockers

- Primary source verification is incomplete.
- CryptoBench files, license, and label schema are unknown.
- Official dataset/tool source records have not been promoted beyond crawl leads.

## Conclusion

Source audit scaffolding is complete enough to begin source verification and dataset planning. It is not sufficient for training.
