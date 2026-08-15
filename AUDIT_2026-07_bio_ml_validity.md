# GNN-PCNA — Biological & ML validity audit (2026-07-21)

HISTORICAL / SUPERSEDED STATUS NOTE (2026-08-15): this July audit is preserved as
historical evidence. Current source of truth is `PROJECT_STATUS.md`; current MD
execution must use `./md.sh` and `md_validation_4070/FINAL_MD_EXECUTION_INSTRUCTIONS.md`.
Do not treat older `run_in_tmux.sh`, direct Python MD commands, or July candidate
windows as current workflow instructions.

**Scope:** the whole pipeline — structure prep, MD validation, graph/feature construction, GNN
training/eval, PCNA inference, and claim-to-evidence alignment.
**Method:** two independent multi-agent code audits. Every finding was **adversarially
re-verified against the actual source** (a second agent tried to *refute* it) before being kept.
- Bio-validity audit `wf_4ee91ba5-47d`: **22 confirmed** (2 high, 6 medium, 14 low), 4 rejected.
- ML-integrity audit `wf_a0b1bcba-09c`: **27 confirmed** (5 high, 8 medium, 13 low), 1 uncertain, 5 rejected.

Rejected findings (9 total) are not listed — they were checked and did not survive verification.

---

## A. Do-first summary

1. **[FIXED & verified]** The MD apo-vs-control comparison was *apples-to-oranges* — the single
   most load-bearing structural bug. Fixed in `md_validation_4070/` v2 and smoke-tested locally
   (see §B). This is what your friend will run.

2. **[NEEDS YOUR DECISION — most important for any submission]** The model that produced your
   **headline numbers** (held-out AUROC 0.8081 / AUPRC 0.3441, AOH gate 0.8676) exists **only as
   compiled `.pyc` bytecode** — no readable `.py` source, no committed checkpoint, and the
   inference driver it references (`scripts/bulk_inference.py`) does not exist. The only *readable*
   model is a **different, simpler** one (25-dim single-branch GraphSAGE, ESM explicitly excluded,
   marked dry-run-only) whose validation numbers are much lower (~0.65 AUROC / ~0.19 AUPRC). **Your
   advertised results currently cannot be reproduced or audited from source.** This is a
   reproducibility/auditability gap, *not* proof the numbers are wrong — but it is exactly what a
   competition judge or reviewer re-runs, and it must be closed before you submit anywhere. See §C.
   → This is the reason your planned **full GNN rerun** matters: rerun from readable, committed
   source so every reported number traces to code anyone can inspect.

3. **[FYI]** The novel-pocket MD evidence to date (1AXC, exploratory) still shows the GNN's novel
   candidate windows (239–243, 28–32, 206–210) were the *most rigid*, not the most dynamic. The
   honest interpretation is unchanged (see the note at the end).

---

## B. Structural / MD bugs — FIXED in `md_validation_4070/` v2 (this push)

All verified locally (prep runs, forcefield parameterizes, energies finite; no CUDA needed for prep).

| Sev | Finding | Fix shipped |
|---|---|---|
| **HIGH** | **Apo/control apples-to-oranges.** `PDBFixer(pdbid=)` fetched the deposited *asymmetric unit*, never the biological assembly. 1W60's ASU is 2 chains that seed **different** crystallographic trimers (their contact is a crystal-packing artifact, not the ring interface); 8GLA's ASU is 4 chains. The AOH1996 pocket only exists at a *real* subunit interface, so the positive-control gate compared non-comparable systems. | `run_md.py` now rebuilds the **biological homotrimer** with gemmi (`make_assembly`) for both structures. Verified: 1W60 → 3 chains (255 aa each), 8GLA → 3 chains (A/B/C), **all 28 pocket residues present on both interface chains**. |
| **HIGH** | Chain count / assembly never enforced (silent skip). | Hard-fails unless exactly `expected_protein_chains` (3) PCNA subunits are produced; writes `prep_audit.json`. |
| MED | 8GLA is 3.77 Å with 92 unmodeled residues rebuilt by PDBFixer — undisclosed quality mismatch vs 1W60 (3.15 Å). | Terminal missing residues are **no longer fabricated**; verified **0 pocket residues** needed rebuilding. `analyze_md.py` now prints the resolution/rebuild caveat next to the gate. |
| MED | `AOH_POCKET` list was hand-curated (dropped IDCL contacts 121/124/129/131, added 42) under a false "6 Å" comment. | Residues now come from the **reproducible derived list** (`pockets/aoh1996.json`, heavy-atom ≤4.5 Å to ZQZ), single source of truth shared by run + analyze. |
| LOW | "peptides stripped" but `removeHeterogens` keeps standard-AA peptides (p21/FEN1). | Only protein chains ≥200 aa are kept — peptides dropped by length (verified: 1AXC's three p21 peptides are removed). |
| LOW | `pbc_sane` = `rmsd.max()<0.6 nm` conflated real motion with PBC artifacts. | Replaced with a **frame-to-frame jump** detector (a box-hop is a spike); smooth large drift is reported as info, not failure. |

**Also delivered:** pocket definition is now parameterized (`pockets/<name>.json`), so validating a
**new GNN-predicted pocket** later is just a new JSON (residues + apo/control PDBs) — with the
positive-control/anti-false-negative machinery intact. Added `run_in_tmux.sh` (detached, survives
SSH drops/reboots, resumes from checkpoints, tailable log). `environment.yml` gains `gemmi`.

---

## C. Reproducibility crisis — the headline model is not auditable from source (NEEDS ACTION)

These are **HIGH** severity, all adversarially confirmed. They are not "bugs" I can patch — they
are about *what is and isn't in the repo*.

- **Advertised ESM2 dual-branch model is `.pyc`-only.** `src/models/cryptic_gnn`, `src/training/{train,loss}`,
  `src/evaluation/score_pockets`, `src/data_processing/graph_construction` exist **only** as
  `.cpython-312.pyc` bytecode — 0 readable `.py` in the entire old `src/` tree. Its loss (imbalance
  handling), AUPRC computation, and any threshold/test-selection are therefore unreviewable.
- **Real PCNA inference driver is missing.** The orchestrator calls `scripts/bulk_inference.py`
  (does not exist) and `python -m src.evaluation.score_pockets` (`.pyc` only). The actual
  score-producing step `scripts/run_v3_inference.py` exists **only** as `.pyc`. `score_pockets`
  is pure post-processing (DBSCAN + AUROC on *precomputed* scores) — it doesn't run the model.
- **Two mutually incompatible pipelines.** Readable governed model = 25-dim single-branch GraphSAGE,
  ESM `NOT_INCLUDED`, no normalization. Results model = 520-dim dual-branch ESM2 `PocketGNNXL` with
  `edge_index_seq`, chain features, virtual node. Anyone "reproducing" from the readable code feeds
  25-dim ESM-free graphs into a model expecting 520-dim — a hard mismatch.
- **Score→residue mapping unverifiable.** Array-index → PDB auth resid → UniProt-P12004 numbering
  is done in compiled code + hand-entered residue lists. An `auth_seq_id` vs `label_seq_id`
  off-by-one or a chain misassignment would silently shift which residues are reported as the pocket,
  and nothing readable validates it.
- **[UNCERTAIN, medium]** The readable rebuild's honest **validation** numbers (~0.65 AUROC /
  ~0.19 AUPRC across 12 runs) are far below the advertised held-out 0.81/0.34. Caveat: those are
  *validation-only* from a model that was never test-evaluated (GATE 5 never run), so it is **not**
  a like-for-like counter-number — but the gap is large enough to resolve explicitly.

**What closing this requires (before any submission):** restore the readable `.py` source for the
model + loss + training + scoring + inference that produced the reported metrics; commit the
checkpoint (`best.ckpt`) and its `best_meta.json`; and state, per number, exactly which
model/features/split produced it. Then confirm the residue-numbering path with a written test.

---

## D. Full findings mapped to your checklist

### Data leakage
| Sev | Finding | Location |
|---|---|---|
| MED | Homology grouping (sequence clusters) never applied across the 4 CV folds → homologs can leak into the validation fold used for model selection. | `scripts/sequence_clustering.py:264` |
| MED | The `.pyc`-only ESM pipeline can't be audited for leakage at all (see §C). | `src/` |
| LOW | A test-fold structure has a null sequence cluster — its homology to train was never checked. | `sequence_clustering.py:260` |

### Label validity
| Sev | Finding | Location |
|---|---|---|
| LOW | Positive-unlabeled labels: all non-annotated residues treated as **hard negatives** in the loss (some "negatives" are just unlabeled). | `phase3_data/labels.py:44` |
| LOW | Novel window 206–210 abuts a known p21 contact (208); 28–32 contains p21 contact 29 — overlap checker only tests conservative cores, under-reporting the PIP-box footprint (risks overstating novelty). | `check_prediction_overlap.py:66` |

### Graph construction
| Sev | Finding | Location |
|---|---|---|
| MED | No crystallographic symmetry expansion; non-target chains dropped → interface pockets (the AOH class!) can be structurally incomplete in the graph. | `phase3_graphs/builder.py:210` |
| MED | A requested target chain absent from the CIF is silently dropped as long as one target chain survives. | `builder.py:213` |
| LOW | Sequence-adjacent residues get **both** a spatial and a sequential edge → backbone neighbours double-counted in message passing. | `builder.py:148` |
| LOW | Model ignores `edge_type`/`edge_distance`; sequential edges even store `inf` distance (carried into every `Data`). | `phase3_model/gnn.py:67`, `graph_loader.py:46` |

### Feature correctness
| Sev | Finding | Location |
|---|---|---|
| MED | Node features are **only** 22-way AA one-hot + 3 quality flags — no SASA/burial/hydrophobicity/secondary-structure/conservation. Geometry enters only via the 8 Å contact graph. | `phase3_graphs/features.py:55` |
| MED | Results-model inference features embed **chain identity** (`chain_onehot`/`cross_chain`) that the governed pipeline explicitly bans — another train/infer divergence. | `features.py:16` |
| LOW | Audited model is single-branch GraphSAGE (no ESM); the "+ESM2 dual-branch" lives in the separate, unverified `.pyc` track. | `features.py:14` |

### Training & evaluation
| Sev | Finding | Location |
|---|---|---|
| MED | Required external baselines (fpocket, P2Rank, PocketMiner) never actually run — only stubs. | `scripts/run_baselines.py:251` |
| LOW | Epoch budget differs: primary 200 vs GNN baselines/ablations 100 (unfair comparison). | `baselines/gnn_trainer.py:100` |
| LOW | Headline mean±SD pools fold **and** seed variance, so "seed variance" isn't isolated. | `summarize_training.py:44` |
| LOW | Per-protein metric single-class guard misses the all-positive case. | `phase3_evaluation/metrics.py:38` |
| LOW | Dead/no-op loop in metric aggregation. | `metrics.py:118` |

### Inference consistency
See §C (all HIGH): missing/`.pyc`-only inference driver, incompatible 25-dim vs 520-dim pipelines,
unverifiable eval()/no_grad, unverifiable residue mapping, no checkpoint on disk.

### Scientific interpretation
| Sev | Finding | Location |
|---|---|---|
| MED | Only production MD (1AXC) is peptide-stripped holo — neither the declared apo (1W60) nor the holo (8GLA); "front face didn't reopen" is confounded by relaxation from a peptide-bound state. | `PHASE5_MD_RESULTS.md:11` |
| LOW | 5E0V mislabeled "apo-WT reference" in the 1AXC pre-registration (it's the S228I + FEN1 variant). | `reports/phase4/md/1axc/pre_registration.md:41` |
| LOW | Phase5 RMSF reference window 118–122 sits inside the flexible IDCL; using it as a "rigid" baseline can make candidates look artificially rigid. Role undocumented. | `phase5_analyze_1axc_md_fixed.py:47` |

### Robustness & failure handling
| Sev | Finding | Location |
|---|---|---|
| LOW | `graph_loader._npz_to_data` trusts `.npz` blindly — no feature-dim / NaN-Inf / edge-bounds / label-domain checks; `edge_attr` carries `Inf`. | `phase3_data/graph_loader.py:46` |
| LOW | Non-numeric/absent CA occupancy silently coerced to 1.0 while bad coords fail closed — inconsistent altloc handling, no warning. | `mmcif_coords.py:153` |
| LOW | Graph-gen CLI swallows all per-structure exceptions, masking systematic code bugs as "data failures". | `phase3_graphs/cli.py:108` |
| LOW | `mmcif.py` scans headers with `startswith` on unstripped lines while `mmcif_coords.py` strips first — divergent parsing of the same CIF. | `mmcif.py:55` |
| LOW | Determinism relies on a single `torch.manual_seed`; no `use_deterministic_algorithms`, no DataLoader generator, no numpy seed. | `train_phase3.py:69` |

### Reproducibility & claim-to-evidence
| Sev | Finding | Location |
|---|---|---|
| MED | Referenced checkpoint `checkpoints/pcna_reproduced/best_meta.json` and **all** model weights are absent. | `train_phase3.py:171` |
| LOW | Hardcoded absolute-path dependency on an out-of-repo data zip blocks clean-env reproduction. | `validate_esm_features.py:45` |
| LOW | No software/env version pinning; run manifests omit library versions and full dataset hash. | `pyproject.toml:13` |
| LOW | Auto-generated manuscript contains factual mis-statements that passed the banned-wording filter. | `paper/manuscript.md:20` |
| MED | Committed MD analysis artifacts are stale vs the current "fixed" script — the chain-aware method was never re-run (headline RMSF numbers unchanged, but not reproducible from the described pipeline). | `outputs/phase5_md/.../analysis_summary.json:34` |

---

## Note on the "novel pocket dynamics" question

The evidence in the repo still shows the GNN's novel candidate pockets were the **most rigid** in
MD, not the most dynamic. The scientifically valid ways forward remain: (1) run the fair,
positive-controlled comparison in this v2 package and report whatever it shows; (2) report the
negative honestly — it qualifies as a result under your own `30_NEGATIVE_RESULT_SUCCESS_CRITERIA.md`;
(3) if you believe a site opens on longer timescales, test it with enhanced sampling (metadynamics)
where "it doesn't open" stays a possible answer. The MD harness must never be tuned to a predetermined
conclusion — that's the one thing that would actually sink the project if a reviewer found it.

*Generated by two adversarially-verified multi-agent audits. Findings cite `file:line` against the
source as of this commit; spot-check any before acting.*
