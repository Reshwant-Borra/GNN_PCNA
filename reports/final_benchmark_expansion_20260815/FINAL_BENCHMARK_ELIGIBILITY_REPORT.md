# Final Benchmark Eligibility Report

Created: 2026-08-15T17:21:16.077348Z
Git commit: `5b2ce676c790c4aac0caa10dc4226b5a924791c0`; dirty worktree: `True`.

## Candidate Inventory

Discovered candidate structure records: **1237**.
Eligible for extraction-method development: **5**.
Excluded: **1232**.

Eligible IDs: `1GQY`, `2HNX`, `2K1V`, `2WER`, `3FU8`

The expanded audit found historical labels and Git-history artifacts, but no additional non-PCNA structures with compatible frozen-checkpoint residue scores, canonical 520-dim graph/label provenance, and a legitimate development role beyond the existing validation set.

## Dataset Roles

- Training split: rejected for extraction-method development.
- Model validation split: eligible only for non-degenerate, non-PCNA structures with frozen-checkpoint scores.
- Checkpoint selection: 8GLA chain-B role; rejected.
- Fine-tuning: 8GLA/PCNA role; rejected.
- Untouched test split: preserved; not consumed to tune extraction.
- PCNA target: 1W60 rejected from selection.
- Positive control: 8GLA rejected from selection.

Established split/label integrity check was rerun from the canonical Git snapshot into `artifacts/final_benchmark_expansion_20260815/split_integrity_520_rerun_from_git_snapshot.json`: `ok=true`, `errors=[]`, graph-manifest hash `69744b548e812697ba9015c6563ed526f1af2e915b1595badb1dd47fd1b4c64f`, with the same six degenerate structures recorded by the canonical report.
Homology/leakage status remains the established `data/results/homology30_audit.json` PASS: no train-to-val/test cluster overlaps and `leakage_detected=false`.

Selection file-read audit remains `pcna_inputs_read_during_selection: []` from the strong robustness audit. No new selection pass read PCNA inputs.

## Benchmark Quality

Protein sizes: {'min': 47, 'median': 428, 'mean': 532.8, 'max': 1116, 'values': [937, 136, 47, 428, 1116]}.
Pocket positive counts: {'min': 6, 'median': 15, 'mean': 19.8, 'max': 39, 'values': [39, 9, 6, 30, 15]}.
Label prevalence by protein: {'1GQY': 0.04162219911813736, '2HNX': 0.06617647409439087, '2K1V': 0.12765957415103912, '2WER': 0.07009346038103104, '3FU8': 0.01344086043536663}.

limited: high-quality independent benchmark remains only five heterogeneous validation proteins; adequate for rejecting obviously brittle extraction changes, not for universal method optimality

## Extraction Comparison

Serious candidate methods compared in the existing robustness grid: fixed absolute threshold, validation-MCC absolute threshold, MCC rank count, MCC rank fraction, chain-aware rank fraction, fixed rank fraction, DBSCAN eps 5/6/7 A, min_samples 3, min cluster size 3, cluster ranking by mean score or mean score x sqrt(size), plus diagnostic mean-rank ensembling.

Current policy grid ID: `mcc_rank_fraction_eps6_ms3_min3_mean_score_sqrt_size`.
Materially better independent policy found: **False**.
LOPO score improvement of best over current: `0.0413`.
Current LOPO mean score: `0.6184`; best LOPO mean score: `0.6597`.

No replacement is frozen because the expanded audit did not add eligible structures and the existing LOPO/bootstrap comparison did not demonstrate a robust, material improvement over the current independently frozen policy.

## PCNA Rerun

No new 1W60 evaluation was run because no independently justified replacement policy was frozen.

## Final Reproducibility Assessment

Mean literal 1W60 Jaccard: `0.6792`.
3/3 core: `11` residues; >=2/3 consensus: `16` residues; union: `20` residues.
Centroid distances (A): 42-43=4.454, 42-44=1.394, 43-44=5.091.
6 A near-overlap: 42-43=0.906, 42-44=1.000, 43-44=0.889.

Classification: **MODERATE / EXPLORATORY PASS**. Literal boundary agreement is moderate, but the three seeds identify the same physical candidate pocket core with strong geometric overlap and high local/global rank concordance.

## Retraining Decision

**RETRAINING NOT JUSTIFIED.** Rankings remain strongly correlated, the pocket location is physically stable, and disagreement is primarily boundary/calibration-related rather than model-level collapse.

## MD Readiness

**PROCEED TO CONTROL-FIRST MD**.

Do not start long candidate production MD before Gate-6 approval. Current sequence is GNN frozen -> structure/preparation validation -> MD parameter validation -> frozen analysis -> 0.1 ns smoke -> analysis validation -> 3 x 5 ns control-first validation -> human Gate-6 -> benchmark on chosen production GPU -> production MD -> frozen final analysis.

Exact first MD command from the repository root: `./md.sh smoke`
