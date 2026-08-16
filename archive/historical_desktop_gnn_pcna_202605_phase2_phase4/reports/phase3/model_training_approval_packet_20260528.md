---
type: human-approval-packet
date: 2026-05-28
gate: first_training_run
governance: docs/scientific_governance/26_HUMAN_REVIEW_GATES.md
status: PENDING_HUMAN_REVIEW
agent: claude-sonnet-4-6
---

# Phase 3 Model / Training Approval Packet — 2026-05-28

## Purpose

This packet proposes a Phase 3 GNN architecture, training constraints, baseline
plan, evaluation plan, stopping conditions, and shortcut/leakage safeguards for
human review and approval before any real training begins.

No model weights, training runs, gradients, or results are presented here.
This is a proposal only. Implementation begins only after the human project owner
signs the decision form at the end of this document.

Prerequisites satisfied:
- Phase 2 complete (split frozen `24dd5e347d880108`, labels frozen).
- First graph release approved (`first_graph_release_approval_20260528.md`).
- Graph artifacts in `data/graphs/` (1,101 structures, 0 failures).

Governance references:
- `docs/scientific_governance/08_MODEL_ARCHITECTURE_CONSTRAINTS.md`
- `docs/scientific_governance/09_EVALUATION_PROTOCOL.md`
- `docs/scientific_governance/10_BASELINE_REQUIREMENTS.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`

---

## 1. Graph Input Summary

The approved MVP graph has the following properties:

| Property | Value |
|---|---|
| Node features | 25-dim float32 (22 one-hot residue identity + 3 binary flags) |
| Spatial edges | Undirected CA-CA, 8.0 Å cutoff |
| Sequential edges | Undirected, consecutive `label_seq_id`, same chain |
| Node labels | {-1 masked, 0 background/unlabeled, 1 positive} |
| Loss mask | `label ≠ -1` participates in loss; `label = -1` is excluded |
| ESM / normalization | Neither present in MVP graphs |
| Avg structure size | 337.6 residues (median 295; range 52–2,598) |
| Positive rate | 16,335 / 351,651 non-masked nodes ≈ **4.6%** |

The sparsity of positive labels (4.6%) has direct consequences for metric
selection and class-weight choices — see Sections 4 and 6.

---

## 2. Proposed GNN Architecture

### 2a. Model Class: Message-Passing GNN (GraphSAGE-style)

**Proposed:** GraphSAGE mean aggregation, 3 layers, fixed hidden dimension.

**Scientific justification:** Residue-level pocket prediction depends on local
structural environment (nearby contacts in 3D and in sequence). A 3-layer
message-passing network has a receptive field covering residues up to 3 hops
away — roughly 20–30 Å in a typical protein — which is sufficient to capture
the spatial pocket context without requiring computationally expensive global
pooling or attention over full structures. GraphSAGE mean aggregation is
documented to generalize well on sparse node classification tasks and is simple
enough to audit for batch-isolation bugs.

**Why not GAT / attention?** Attention introduces additional learnable parameters
and can more easily learn shortcut patterns (e.g., attending to structurally
anomalous residues correlated with crystal packing). GAT is included as a
required ablation baseline, not as the primary model.

**Why not global virtual node?** A virtual node aggregates across all residues in
a PyG batch. With mixed-protein batches, a naive `h.mean(dim=0)` would aggregate
across proteins, causing batch-isolation failure (forbidden by governance/08).
Correct batch-aware pooling (`scatter_mean` over `batch` tensor) is possible but
adds complexity. MVP excludes the virtual node; it may be added in a later
approved revision with the required batch-isolation unit test.

### 2b. Proposed Architecture Specification

```
Input: x ∈ ℝ^(N × 25)   [25-dim node features]
       edge_index ∈ ℤ^(2 × E)
       edge_type ∈ {0, 1}^E   [spatial / sequential]
       batch ∈ ℤ^N             [protein membership]

Layer 1: SAGEConv(25 → H, aggr='mean') + ReLU + Dropout(p)
Layer 2: SAGEConv(H → H,  aggr='mean') + ReLU + Dropout(p)
Layer 3: SAGEConv(H → H,  aggr='mean') + ReLU

Head:    Linear(H → 1)   → logit per residue

Output:  logit ∈ ℝ^N   [BCEWithLogitsLoss-compatible; NO sigmoid during training]
```

Proposed hyperparameter ranges (to be tuned on validation only):

| Hyperparameter | Proposed range | Notes |
|---|---|---|
| Hidden dim `H` | {64, 128} | Start small; protein structures are small graphs |
| Dropout `p` | {0.0, 0.3} | Evaluate via validation AUPRC |
| Learning rate | {1e-3, 3e-4} | Adam optimizer |
| Batch size | {16, 32} structures | Subject to GPU memory |
| Epochs | up to 100 | Early stopping on validation macro-AUPRC |
| Early stopping patience | 10 epochs | |

All hyperparameter choices are locked before test evaluation. No test-set
tuning is permitted.

### 2c. Loss Function

**BCEWithLogitsLoss with positive class weight.**

Positive class weight `pos_weight` is computed from **training-fold labels only**:

```
pos_weight = (n_bg_train) / (n_pos_train)
```

where `n_bg_train` is the count of background/unlabeled nodes in the training
fold and `n_pos_train` is the count of positive-label nodes. Masked nodes
(`label=-1`) are excluded from both counts.

`pos_weight` must **not** be computed from validation or test labels. This is a
hard rule under governance/08.

### 2d. Batch Isolation Requirement

Before the first training run, a batch-isolation unit test must pass:

> Batch proteins A and B together. Verify that protein A's logits (extracted by
> `batch == 0`) match single-protein inference on A within 1e-5 tolerance.
> Repeat for B. Repeat with proteins batched in reversed order.

This test is mandatory under governance/08 and must be added to `tests/phase3/`
before training begins.

### 2e. Cross-Validation Strategy

4-fold cross-validation using the frozen split:

| Run | Train folds | Validation fold | Test |
|---|---|---|---|
| Fold-0 | train-1, train-2, train-3 | train-0 | held out |
| Fold-1 | train-0, train-2, train-3 | train-1 | held out |
| Fold-2 | train-0, train-1, train-3 | train-2 | held out |
| Fold-3 | train-0, train-1, train-2 | train-3 | held out |

Model selection: the model checkpoint with the best **validation macro-AUPRC**
across all seeds for a given fold is selected. The fold with the best overall
validation macro-AUPRC is the primary model unless variance across folds
indicates instability (see stopping conditions).

Test evaluation is run **once** on the frozen test fold (214 structures) using
the selected checkpoint. No re-evaluation, no threshold re-selection.

### 2f. Seeds

Minimum 3 random seeds; 5 preferred. Seed values must be fixed before training
and recorded in the run manifest. All seeds must be reported; no seed may be
hidden.

---

## 3. Baseline Plan

The following baselines are required under governance/10 before any superiority
or comparative claims. All baselines use the same frozen split.

| Baseline | Tool / Method | Runs on | Notes |
|---|---|---|---|
| **Random** | Uniform random score ∈ [0,1] per residue | Same 1,101 structures | Establishes non-trivial floor |
| **Solvent exposure** | RSA from DSSP or equivalent | Same CIF files | Simple structural heuristic |
| **fpocket** | fpocket ≥ 4.0 | Same CIF files | Geometric cavity detector |
| **P2Rank** | P2Rank ≥ 2.4 | Same CIF files | ML-based pocket ranker |
| **PocketMiner** | PocketMiner published code | Same CIF files | Cryptic-pocket specialist; run on our split |
| **Basic GCN (1-layer)** | Single SAGEConv layer, H=64 | Same graphs | Architecture ablation |
| **GAT (2-layer)** | GATConv, H=64, 4 heads | Same graphs | Attention model baseline |
| **No-edge-type baseline** | Model without edge-type feature | Same graphs | Tests value of spatial/sequential distinction |

**Comparison constraints (governance/10):**
- PocketMiner numbers from the published paper must **not** be used as our
  comparison; PocketMiner must be run on the Phase 2 split with matching labels.
- fpocket/P2Rank produce pocket volumes/scores, not per-residue probabilities.
  Scores must be mapped to residue level (e.g., residue in top-N pocket = positive
  score) and compared under the same AUPRC/top-k framework.
- Baseline provenance: command, version, output hash, and run date logged per run.

---

## 4. Evaluation Plan

All metric choices are **pre-specified** here. No metric may be added, removed,
or redefined after viewing test-set output.

### 4a. Primary Metric

**Macro-AUPRC** (area under precision-recall curve, averaged over proteins).

Rationale: positive labels are sparse (~4.6%). AUROC is inflated under extreme
class imbalance. Macro-AUPRC is more informative about per-protein pocket
recovery and is not dominated by the large number of background residues in
dense micro-averaging.

### 4b. Full Metric Set

| Metric | Aggregation | Notes |
|---|---|---|
| AUPRC | macro and micro | Primary (macro); micro reported for completeness |
| AUROC | macro and micro | Secondary diagnostic |
| Top-k residue recovery | per-protein, k = 5, 10, 20 | Fraction of positives in top-k ranked residues |
| Precision@k | per-protein, k = 5, 10, 20 | Fraction of top-k predictions that are positive |
| Expected calibration error | model-wide | Scores described as probabilities only if calibration passes |
| Bootstrap 95% CI | over proteins, N=1000 | All primary metrics |
| Per-protein table | all metrics | Inspect for outlier structures |
| Seed mean ± SD, range | all primary metrics | Show all seeds |

### 4c. Pre-Specified Success Criteria

An improvement over baselines is considered meaningful only if:

1. Macro-AUPRC exceeds both the random baseline and at least one geometric
   baseline (fpocket or P2Rank) on the same split.
2. The improvement survives shortcut ablations (chain-ID and graph-size checks).
3. Bootstrap CIs do not overlap between model and best geometric baseline.
4. At least one seed meets the criterion; seed mean also exceeds baselines.

These are **internal computational performance criteria**, not external or
clinical claims. Governance/14 applies to all result language.

### 4d. Test-Set Policy

- Test set (214 structures) is evaluated **once** after: model frozen, thresholds
  frozen, baseline runs complete, report plan frozen.
- No threshold tuning, metric selection, or re-evaluation on test.
- A test-used-once log entry is required in `wiki/log.md` at evaluation time.

---

## 5. Stopping Conditions

From `docs/scientific_governance/19_STOP_CONDITIONS.md`. The following apply
specifically to Phase 3 training and evaluation:

| Condition | Trigger | Action |
|---|---|---|
| **Leakage found** | Shared protein or homolog across train/test | Freeze all artifacts; rebuild split |
| **Graph-label mismatch** | Node count or label count mismatch during data loading | Freeze training; re-audit graphs |
| **Shortcut detected** | Chain-ID or graph-size ablation reveals spurious correlation | Freeze model; ablate or remove feature |
| **Batch isolation fails** | Batched logits differ from single-protein logits | Fix architecture; rerun test |
| **Metrics unstable** | Seed variance changes conclusion (e.g., one seed shows superiority, others do not) | Report variance honestly; downgrade claims |
| **Null baseline wins** | fpocket/P2Rank/random matches or beats model under same split | Report honestly; do not hide; do not remove from report |
| **Provenance broken** | Missing hash, command, or seed in any run manifest | Freeze result; re-run from manifest |
| **Claim exceeds evidence** | Model output described with forbidden wording | Rewrite or remove claim |
| **Positive-control failure** | AOH1996/8GLA site (PCNA positive control) not recovered in PCNA inference | Flag; do not use as evidence of model quality; investigate |

---

## 6. Shortcut and Leakage Safeguards

### 6a. Features Already Excluded (graph policy)

- Chain ID (not in trainable features; metadata-only).
- Residue number / insertion code (not in trainable features).
- Fold, cluster ID, split assignment (not in graphs).
- ESM embeddings (not present in MVP graphs).

These exclusions are enforced at graph generation and hash-locked in the
feature-definition hash (`80049e38d0f6ccf6c59f045bf977b69b...`).

### 6b. Required Ablation Runs (before claims)

These must be run and reported; results must not be hidden:

| Ablation | What it tests | When |
|---|---|---|
| **No-sequential-edges** | Value of chain-connectivity information | After first training |
| **No-spatial-edges** | Value of 3D contact information | After first training |
| **Residue-identity shuffled** | Dependency on amino-acid identity | After first training |
| **Graph-size correlation** | Does score correlate with protein size? | After first training |
| **Per-protein metric inspection** | Does one outlier structure dominate micro metrics? | After first training |
| **Positive-label rate correlation** | Does score correlate with structure's positive density? | After first training |

### 6c. Sequence-Based Leakage Safeguard

The frozen 30% identity clustering ensures no protein-family leakage across
train/test at the split level. However, within-protein shortcut risks remain
(e.g., pocket residues clustered at specific sequence positions). These are
monitored via the per-protein metric table and residue-identity ablation.

### 6d. Normalization Policy

No normalization statistics have been computed. If normalization is added in a
future revision, statistics must be fit exclusively on training-fold node
features. Governance/07 forbids fitting on validation or test structures.

### 6e. PCNA Holdout Safeguard

PCNA cluster (cluster_id_30=1168) is not present in train or validation. Any
inference on PCNA structures (`5e0v` or similar) is treated as a positive-control
check only — not as evidence of model generalization — and must be framed as such
per governance/14.

---

## 7. Implementation Sequence (after approval)

The following order is required:

1. **[AGENT]** Add batch-isolation unit test to `tests/phase3/`. Must pass before training.
2. **[AGENT]** Implement data loader: reads `.npz` + `_meta.json` from `data/graphs/`,
   returns PyG `Data` objects; applies frozen split; excludes masked nodes from loss.
3. **[AGENT]** Implement model: `phase3_model/gnn.py`, satisfying `ModelInterface` contract.
   Must pass static forbidden-pattern scan and batch-isolation test.
4. **[AGENT]** Implement training loop: `phase3_training/trainer.py`. Remove dry-run guard
   only after GATE 2 is signed (separate approval after this packet is approved).
5. **[AGENT]** Implement evaluation: `phase3_evaluation/metrics.py`. Pre-specified metrics
   only; no test evaluation until model is frozen.
6. **[HUMAN — GATE 2]** First-training sign-off: record after reviewing batch-isolation test
   and architecture implementation. Then agent may run first real training run.
7. **[AGENT]** Run baselines (geometric tools first, then GNN ablations).
8. **[HUMAN — GATE: first PCNA prediction]** Before any PCNA inference is interpreted.

---

## 8. What This Packet Does Not Approve

This packet, if approved by the human reviewer, authorizes:
- Implementation of the proposed architecture and training loop.
- Removal of the dry-run guard after a separate GATE 2 sign-off.
- Running baseline tools.

This packet does **not** authorize:
- Real training (requires separate GATE 2 sign-off after implementation review).
- Test-set evaluation before model and baselines are frozen.
- PCNA prediction interpretation (requires its own gate).
- MD runs (requires its own gate).
- Scientific claims of any kind.

---

## Human Review Decision Form

**Decision ID:** `phase3_model_training_plan_20260528`

**Reviewer:** human project owner

**Date:** ___________

**Decision:** [ ] approved  [ ] approved with revisions (list below)  [ ] rejected

**Revisions required (if any):**

1. ___________
2. ___________

**Limitations and follow-up actions acknowledged:**

- [ ] Batch isolation test required before first training run.
- [ ] Baselines must run before claims.
- [ ] Stopping conditions will be applied; no hiding of negative results.
- [ ] Test set evaluated once only, after frozen model and baselines.
- [ ] All claims subject to governance/14 (no forbidden wording).

**Formal decision record will be:**
`reports/phase3/model_training_decision_YYYYMMDD.md`
