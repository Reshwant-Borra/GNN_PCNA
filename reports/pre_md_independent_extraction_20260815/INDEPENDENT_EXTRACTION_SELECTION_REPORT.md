# Independent Extraction Selection Report

Created: 2026-08-15T16:21:10.778511Z
Predeclared spec: `artifacts/pre_md_independent_extraction_20260815/predeclared_extraction_selection_spec.json`
Predeclared spec SHA-256: `87c0317f66cda0b2dff8715710fc32b64a67429367a33c87689432f6f6be2b32`
Frozen policy: `artifacts/pre_md_independent_extraction_20260815/frozen_extraction_method.json`
Frozen policy SHA-256: `24979c81c86c012fc8cbb9d665f6a5294da6de2e30a28eb71827abfb5009abcf`

## Independence

Selection used only non-PCNA calibration score/label rows for 1GQY, 2HNX, 2K1V, 2WER, and 3FU8. It did not read 1W60 score files.

## Eligibility

| PDB | Eligible | Rationale |
| --- | --- | --- |
| 1GQY | True | non-PCNA, labels n=39, homology audit PASS |
| 2HNX | True | non-PCNA, labels n=9, homology audit PASS |
| 2K1V | True | non-PCNA, labels n=6, homology audit PASS |
| 2WER | True | non-PCNA, labels n=30, homology audit PASS |
| 3FU8 | True | non-PCNA, labels n=15, homology audit PASS |
| 2CNN | False | degenerate validation labels in canonical clean split: n_positive=4 < min_positive=5 |
| 8GLA | False | PCNA positive-control/fine-tuning/checkpoint-selection structure; forbidden for independent extraction selection |
| 1W60 | False | final PCNA target; forbidden for extraction-method selection |

## Results

| Policy | Eligible | Composite | F1 | Recall | Precision | Label Jaccard | Seed Jaccard | Valid clusters |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| independent_mcc_rank_fraction_size_weighted_cluster | True | 0.6328 | 0.3081 | 0.2703 | 0.4305 | 0.1965 | 0.5726 | 0.9333 |
| independent_mcc_rank_fraction_primary_cluster | True | 0.6139 | 0.3098 | 0.2686 | 0.4678 | 0.1976 | 0.4882 | 0.9333 |
| independent_mcc_rank_count_primary_cluster | True | 0.5712 | 0.2767 | 0.3729 | 0.3936 | 0.1666 | 0.4449 | 1.0000 |
| independent_mcc_rank_chain_fraction_primary_cluster | True | 0.4940 | 0.2374 | 0.2108 | 0.3699 | 0.1401 | 0.4797 | 0.8667 |
| fixed_0p4_primary_cluster | True | 0.3872 | 0.2660 | 0.2914 | 0.3672 | 0.1651 | 0.2880 | 0.8667 |
| independent_mcc_abs_primary_cluster | False | 0.2712 | 0.1868 | 0.1708 | 0.3164 | 0.1114 | 0.4483 | 0.6667 |

Selected policy: `independent_mcc_rank_fraction_size_weighted_cluster`.

This report is not a PCNA stability result.
