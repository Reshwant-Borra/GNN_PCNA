# Final 1W60 Three-Seed Stability Report

Created: 2026-08-15T16:21:23.468624Z
Frozen policy: `artifacts/pre_md_independent_extraction_20260815/frozen_extraction_method.json`
Frozen policy SHA-256: `24979c81c86c012fc8cbb9d665f6a5294da6de2e30a28eb71827abfb5009abcf`
Policy: `independent_mcc_rank_fraction_size_weighted_cluster`

## Gate

Predeclared PASS requires valid primary clusters in all three seeds, literal mean pairwise Jaccard >= 0.50, consensus >= 8 residues, and positive primary/runner-up margin where a runner-up exists.

## Seed Results

| Seed | Selected before clustering | Primary cluster | Cluster count | Runner-up margin | Mean score | Max score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 42 | 31 | 16 | 3 | 0.381837 | 0.3651 | 0.7123 |
| 43 | 34 | 13 | 4 | 0.346514 | 0.2455 | 0.6273 |
| 44 | 23 | 18 | 2 | 0.822633 | 0.2577 | 0.4230 |

## Agreement

Literal mean pairwise Jaccard: `0.6792`.

| Pair | Literal Jaccard | Symmetry-normalized supplementary Jaccard | Spearman | Top-50 Jaccard |
| --- | ---: | ---: | ---: | ---: |
| 42-43 | 0.7059 | 0.7059 | 0.8497 | 0.6129 |
| 42-44 | 0.7000 | 0.7000 | 0.8069 | 0.6667 |
| 43-44 | 0.6316 | 0.6316 | 0.8787 | 0.6129 |

Consensus residues: `16`.

PRE-MD STABILITY: **PASS**

Interpretation: this gate only supports a governed MD handoff. It is not evidence of binding or druggability.
