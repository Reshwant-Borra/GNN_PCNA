# Split Protocol

## Purpose

Define leakage-resistant train/validation/test splits for residue-level pocket prediction.

## Hard Rules

- Split before graph generation.
- Split by protein system, UniProt ID, family, sequence cluster, and apo/holo group wherever possible.
- Sequence clustering is required before final splits.
- Structural similarity review is required for proteins near the decision boundary.
- Apo/holo structures and ligand variants of the same protein must be grouped.
- Homologs are not allowed across train, validation, and test.
- PCNA-specific final-claim structures cannot influence model selection.
- Validation is used only for model selection.
- Test is used once after model, thresholds, baselines, and reporting plan are frozen.
- 8GLA/AOH1996 may be a positive-control gate only under its declared leakage status.

## Acceptable Split Types

- Family-level split with sequence-cluster grouping.
- Protein-system split grouping apo/holo and ligand variants.
- Benchmark-provided split only if audited for homology, apo/holo, and PCNA leakage.
- PCNA final-claim holdout where PCNA structures are excluded from training and tuning.

## Unacceptable Split Types

- Residue-level random split.
- Graph-level random split without grouping systems.
- Splitting apo and holo versions across sets.
- Recomputing splits until metrics look good.
- Combining validation and test for headline model selection.

## Minimum Split Audit Outputs

- `split_assignment.json` with train/val/test arrays.
- `split_hash.txt`.
- Sequence cluster table with thresholds and tool version.
- Apo/holo grouping table.
- Structural similarity review notes.
- PCNA isolation statement.
- Positive-control status for 8GLA/AOH1996.

## Split Assignment File Requirements

```json
{
  "split_id": "phase2_<date>_<hash>",
  "created_by": "<person_or_agent>",
  "created_at": "<timestamp>",
  "sequence_clustering_tool": "<tool_version>",
  "structural_review_method": "<method>",
  "train": [],
  "validation": [],
  "test": [],
  "heldout_pcna_final_claim": [],
  "positive_controls": [],
  "excluded": [],
  "hashes": {}
}
```

## Forbidden Actions

- Tuning focal-loss alpha, label thresholds, graph thresholds, or model architecture on validation/test distributions.
- Moving systems between splits after seeing results.
- Using test results to decide whether to run more seeds.
- Treating PCNA positive-control recovery as independent test evidence if PCNA was tuned.

## Required Checks

- No shared UniProt ID across splits.
- No high-identity homologs across splits.
- No same PDB biological assembly group across splits.
- No apo/holo pair across splits.
- No ligand-bound variant leakage.
- Split hash stored in every graph, checkpoint, and metrics report.

## Examples Of Failure

- `8GLA` is used to tune an AOH gate, then AOH recovery is reported as final validation.
- A protein family appears in train and test under different PDB IDs.
- Split is run after graphs are generated and graph cache already encoded label or normalization choices.

## Prevention

Create split manifest first, then generate graphs split-aware. Make graph-generation commands require `--split-assignment`.

## Compliance Artifact

`data/splits/phase2_split_<hash>.json` and `reports/phase2/split_audit.md`.

## If Leakage Is Discovered

Freeze all affected metrics, checkpoints, and reports. Mark them `LEAKED_DO_NOT_CLAIM`. Rebuild the split, regenerate graphs, retrain, rerun baselines, and issue a leakage note.
