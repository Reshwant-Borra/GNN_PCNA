# Assumption Registry

## Purpose

No undocumented assumption may drive Phase 2 implementation, evaluation, MD interpretation, or claims. This file defines the required registry format and starter assumptions.

## Hard Rules

- Every scientific assumption must be registered before code depends on it.
- Assumptions must distinguish evidence, inference, and convenience.
- Low-confidence assumptions may support exploratory analysis but not final claims.
- Any assumption touching PCNA biology, 8GLA/AOH1996, ATX-101, PIP-box/APIM interfaces, MD, split design, labels, or metrics requires owner review.

## Registry Template

| Field | Required content |
|---|---|
| Assumption ID | Stable ID such as `ASM-PCNA-001` |
| Assumption statement | One falsifiable sentence |
| Category | Dataset, label, split, model, PCNA biology, MD, evaluation, claim |
| Why we believe it | Evidence summary, not vibes |
| Supporting sources | Source index IDs, DOI/PDB/UniProt IDs, or registered context pack |
| Confidence level | High, medium, low |
| What would make it false | Concrete falsifier |
| Failure consequence | What breaks if false |
| Verification method | Audit, experiment, literature review, baseline, MD analysis, human review |
| Verification status | Proposed, under review, verified, rejected, deprecated |
| Owner | Person or agent role |
| Last reviewed date | ISO date |

## Example Assumptions

| ID | Assumption | Category | Confidence | Verification |
|---|---|---|---|---|
| ASM-POCKET-001 | Cryptic/allosteric pockets can be partially inferred from static or ensemble protein structures. | Model | Medium | Benchmark against curated pocket datasets and report limitations. |
| ASM-PCNA-001 | AOH1996/8GLA can function as a positive-control pocket-recovery check for PCNA-targeting region recovery. | PCNA biology | Medium | Verify 8GLA was excluded from model tuning before using it as independent evidence; otherwise mark as sanity check only. |
| ASM-MD-001 | MD can provide supportive evidence for flexibility or accessibility but cannot alone prove therapeutic relevance. | MD | High | Enforce [13_MD_VALIDATION_RULES.md](13_MD_VALIDATION_RULES.md). |
| ASM-EVAL-001 | Residue-level GNN outputs can be evaluated using top-k recovery and per-protein metrics. | Evaluation | High | Report per-protein top-k, AUROC, AUPRC, calibration, and CIs. |
| ASM-SPLIT-001 | PCNA-specific structures must not influence model tuning if used for final PCNA claims. | Split | High | Split audit and positive-control audit. |

## Forbidden Actions

- Encoding "PCNA is druggable" as a model target without evidence.
- Treating AOH1996 recovery as proof of novel-site validity.
- Assuming MD must confirm pocket opening.
- Assuming AlphaFold confidence equals pocket reality.
- Assuming label proximity equals biological binding-site truth.

## Required Checks

- Before coding: list assumptions used by the task.
- Before training: verify all dataset, label, and split assumptions are reviewed.
- Before MD: verify MD hypothesis and alternative outcomes are registered.
- Before claims: verify every claim links to registered assumptions and evidence.

## Examples Of Failure

- A script hardcodes PIP-box residues as negatives because the novel site should be outside the known interface.
- A report says "therapeutic target" because PCNA is cancer-relevant and the model scored a region highly.
- An MD workflow interprets no pocket opening as simulation failure instead of evidence against the hypothesis.

## Prevention

Add assumption IDs to configs, reports, and code comments where scientific behavior is encoded. Missing assumption ID means the task must pause and document the assumption.

## Compliance Artifact

`docs/scientific_governance/DATASET_REGISTRY.md`, config files, and reports must cite assumption IDs. A registry export must be included in `reports/phase2/assumption_audit.md`.

## If The Rule Fails

Stop the affected implementation path. Register the assumption, review it, and rerun any result that depended on the undocumented assumption.
