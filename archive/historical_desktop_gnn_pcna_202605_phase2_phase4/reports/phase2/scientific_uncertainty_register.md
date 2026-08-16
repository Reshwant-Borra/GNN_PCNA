# Scientific Uncertainty Register

Date: 2026-05-27
Created by: Codex
Status: DRAFT

| ID | Uncertainty | Category | Evidence status | Impact | Current handling | Owner | Review date |
|---|---|---|---|---|---|---|---|
| UNC-DATA-001 | CryptoBench file inventory, license, and label schema are unknown. | dataset/label | missing | blocking | Do not adopt CryptoBench; audit source first. | human reviewer | 2026-05-27 |
| UNC-DATA-002 | Whether BioLiP/BioLiP2/scPDB/PDBbind are in scope or background-only is unresolved. | dataset/label | missing | high | Keep as source leads only. | human reviewer | 2026-05-27 |
| UNC-SPLIT-001 | Sequence clustering tool and threshold are not chosen. | split | missing | blocking | Do not freeze splits. | human reviewer | 2026-05-27 |
| UNC-SPLIT-002 | PCNA final holdout, positive-control, and exclusion structure lists are not frozen. | split/PCNA | missing | blocking | Do not assign PCNA structures to splits. | human reviewer | 2026-05-27 |
| UNC-LABEL-001 | Phase 2 label definition is not frozen. | label | missing | blocking | Use label template only; do not generate labels. | human reviewer | 2026-05-27 |
| UNC-BIO-001 | Biological sanity cannot be completed until candidate datasets, labels, chains, and structures exist. | PCNA/dataset | missing | blocking | Keep biological sanity report as pending review template. | human reviewer | 2026-05-27 |
| UNC-HUMAN-001 | Mandatory human reviewer identity or role is not recorded. | dataset/split/label | missing | blocking | Human gates cannot pass. | project owner | 2026-05-27 |
| UNC-REPO-001 | Fresh Phase 2 implementation branch/path is not confirmed. | provenance | missing | high | Do not treat any implementation artifact as canonical yet. | project owner | 2026-05-27 |

## Governance

- `docs/scientific_governance/35_SCIENTIFIC_UNCERTAINTY_REGISTER.md`

## Conclusion

High-impact and blocking uncertainties remain. The project is ready for dataset planning only.
