# Project Canonical Status

Last updated: 2026-05-24T19:05:16Z
Updated by: research_os.bootstrap
Status: needs_review

## Project goal

GNN-PCNA + molecular-dynamics validation: identify candidate pocket-associated
residues on PCNA, assess them with computational baselines and MD, and produce a
manuscript whose claims are proportional to the evidence.

## Current research question

Can a leakage-clean GNN identify candidate AOH1996-associated pocket residues
on PCNA that hold up under structural realism and MD analysis?

## Current hypothesis

There exists a pocket-associated residue region near known AOH1996 contacts
that a GNN can flag with above-baseline performance under leakage-clean splits.

## Current status summary

Dataset status: see DATASET_REGISTRY.md (treat as needs_review).
Model status: see MODEL_REGISTRY.md (treat as needs_review).
Validation status: see VALIDATION_STATUS.md (treat as inconclusive by default).
Paper status: drafting; claim wording governed by CURRENT_CLAIMS.md.

## Current blockers

- ResearchOS agents have not yet completed a clean full-audit pass.
- All headline metrics, claims, and figures are pending independent verification.

## Next steps

1. Run `python -m research_os audit --repo .`.
2. Triage findings.
3. Re-run with corrected splits / regenerated artifacts as needed.
