# GNN-PCNA — Full Code Audit (2026-07-29)

Scope: all three trees in play —

| Tree | Path | Branch | Role |
|---|---|---|---|
| Production model | `C:/Users/advay/gnn_xl_worktree` | `graph-leakage-fix` | V1/V2/XL model, training, MD, UI — **produced the headline numbers** |
| Governed rebuild | `GNN_PNCA/Desktop/GNN_PCNA` | `advay-parallel-track` | Phase 2/3 governed intake, labels, graphs, metrics |
| Public release | `GNN-PCNA-public` | — | github.com/advaycode/gnnpcna |

193 Python files / ~33k LOC (governed + orchestration) plus ~16.7k LOC (production).
Test suites both green at audit time: **93 passed** (governed), **22 passed** (production).

This audit deliberately does **not** re-report the 63 findings in
`docs/BUG_LEDGER_2026-07-17.md`. That sweep covered the MD / pocket-dynamics
surface. This one covers what it did not: training, losses, metric aggregation,
label generation, feature provenance, and the release surface — plus verification
of which of its "FIXED" claims actually reached shipping code.

Findings marked **[verified]** were reproduced by execution, not inferred.

---

## A. Release & branch state — the highest-impact issues

### A1 · HIGH — The public repo ships the known-buggy code
`GNN-PCNA-public` (github.com/advaycode/gnnpcna, last commit 2026-07-03) contains
the pre-fix versions of every file the private branches repaired:

| Bug | Public repo | Fixed on |
|---|---|---|
| BUG-020 `rel_pos` global index | `graph_construction.py:205` `rel_pos = i / max(N-1,1)` | `graph-leakage-fix` |
| BUG-021 array-index backbone edges | `graph_construction.py:285` `arr_idx = np.arange(N)` | `graph-leakage-fix` |
| BUG-023 virtual node batch mixing | `cryptic_gnn.py:317` `h_s.mean(dim=0)`, no per-graph pool | `graph-leakage-fix` |
| SASA silent-zero | `parse_pdb.py:83` `except Exception:` with no warning | `fix-pocket-dynamics` |
| Unsorted pocket list | `score_pockets.py:46` returns unsorted despite docstring | `fix-pocket-dynamics` |

The last one is user-visible: `cluster_pocket_residues` documents "sorted by
mean_score descending" and returns insertion order, so anyone reading
`pockets[0]` as the top pocket gets an arbitrary cluster.

### A2 · HIGH — Every fix is stranded on an unmerged branch
`main` last moved **2026-06-17**. `fix-pocket-dynamics` (07-17),
`graph-leakage-fix` (07-23) and `advay-parallel-track` (07-23) are all unmerged.
Consequence: the reported metrics still come from the **pre-fix** pipeline, and
there is no single branch where all fixes coexist.

### A3 · MEDIUM-HIGH — The BUG-022 leakage control is implemented but never invoked
`zero_chain_onehot` defaults to `False` and is passed by **zero of 20 call
sites** — including both graph entry points (`build_graphs.py:87`,
`build_graphs_xl.py:77`). Every graph in `data/graphs/` therefore still carries
the chain one-hot at dims 37:40, which is exactly the channel that lets the model
distinguish identical subunits and shortcut the A/B-only ground truth.
`KNOWN_BUGS.md` describes it as "exposed as an off-by-default flag" — accurate,
but it means the leakage path is open in every artifact, not closed.

### A4 · MEDIUM — `KNOWN_BUGS.md` contradicts `E006`
BUG-020/021/022 are listed "**open** (requires retrain)", while
`docs/experiments/E006_graph_leakage_fix.md` concludes the fixes are applied,
verified against a 86-graph rebuild, and a net win (AUPRC +0.096/+0.120 over
3 seeds) — "Recommended for adoption." The code on `graph-leakage-fix` does have
020/021 fixed. The ledger is stale.

---

## B. Training & loss — confirmed defects

### B1 · HIGH — `train.py` silently ignores a missing `--resume` checkpoint
`src/training/train.py:307`
```python
if args.resume:
    ckpt = Path(args.resume)
    if ckpt.exists():
        model.load_state_dict(...)
```
No `else`. A typo'd or moved path trains **from scratch**, and `best_meta.json`
still records `"resume_ckpt": <that path>` (line 381). The provenance record then
asserts a fine-tune that never happened. Every PCNA fine-tune goes through this
path. Add a hard failure.

### B2 · MEDIUM-HIGH — `focal_loss` runs BCE on sigmoid probabilities → gradient explosion **[verified]**
`cryptic_gnn.py:369` calls `F.binary_cross_entropy` on the model's already-
sigmoided output. Reproduced with one saturated node:

```
loss = 33.36   (finite — BCE clamps log at -100, so nothing looks wrong in the log)
grad = 1.67e11
```

The loss curve stays clean while the gradient is ~1e11. `clip_grad_norm_(1.0)`
in `train_epoch` then rescales the **whole** gradient vector by ~6e-12, so that
step's learning signal for every other parameter is destroyed. Use
`BCEWithLogitsLoss` semantics (return logits from the model, sigmoid only at
inference) or clamp scores into `[eps, 1-eps]`.

### B3 · MEDIUM — `ranking_loss` samples by array order, not randomly **[verified]**
`cryptic_gnn.py:387` takes `scores[pos_mask][:n_pos]` and `scores[neg_mask][:n_neg]`
— the *first* positives/negatives in residue order. Reproduced with an identical
score multiset, reordered:

```
loss(easy positives first) = 0.000000
loss(hard positives first) = 0.172500
```

`n_pos` is capped at 32, so for any structure with >32 positive residues the
C-terminal positives are **never** sampled. Sample with `randperm`.

### B4 · LOW-MEDIUM — `symmetry_loss` key collision on negative residue numbers **[verified]**
`cryptic_gnn.py:412` packs `key = batch * resid_range + resid` with
`resid_range = resid.max()+1`, which is unsound for negative resids (legal in the
PDB — expression tags, cloning artifacts):

```
resid=[5, -1]  batch=[0, 1]  resid_range=6  ->  keys=[5, 5]   COLLISION
symmetry_loss = 0.320000     (correct value: 0.0)
```

Residues from two different proteins get penalised as symmetry-equivalent. Bites
only in `--phase finetune` with `batch_size>1`. Offset by `resid.min()` or use
`torch.unique(..., dim=0)` on the stacked pair.

### B5 · MEDIUM — Model selection uses a different metric than the paper reports
`eval_epoch` (`train.py:264`) pools all residues from all proteins and computes a
single **micro**-AUROC, and `is_best` selects on it. The governed protocol
(`09_EVALUATION_PROTOCOL.md`) and the reported results use **macro** metrics.
Scores are not calibrated across proteins and positive rates differ, so the
selected checkpoint is optimised for a metric that is not the one defended.

### B6 · LOW — Dead and mis-advertised loss module
`src/training/loss.py` is dead (correctly noted in `src/training/__init__.py`),
but `agents/mcp_server.py:353` still lists it as a live component
`"Loss — focal+rank+sym"`. It is fixed-alpha focal only. `standardize_chains`
(`parse_pdb.py:183`) has no callers.

---

## C. Metric aggregation (governed tree)

### C1 · MEDIUM — Redundant guard leaves all-positive proteins unhandled, and the two headline metrics disagree **[verified]**
`phase3_evaluation/metrics.py:38,50`
```python
if y.sum() == 0 or (y == 0).all():   # both conditions mean "all zeros"
```
The intended second case — **all positives** — is not guarded. Verified downstream
behaviour for such a protein:

```
average_precision_score(all-positive) = 1.0    -> INCLUDED in macro_auprc (the PRIMARY metric)
roc_auc_score(all-positive)           = nan    -> DROPPED from macro_auroc
```

So one degenerate protein silently contributes a perfect 1.0 to the primary
metric while being excluded from the secondary — different denominators for the
two numbers reported side by side. `warnings.simplefilter("ignore")` suppresses
sklearn's `UndefinedMetricWarning`, so there is no trace. Latent with current
data (no all-positive protein present), but it is a metric-integrity hole.
On sklearn <1.7 the same path raises `ValueError` instead — the module's
behaviour is sklearn-version-dependent.

### C2 · LOW — Dead loop
`metrics.py:118-120` assigns two unused locals inside a `for` and does nothing:
```python
for k in _TOP_K_VALUES:
    key = f"top_{k}_recovery"
    pkey = f"precision_at_{k}"
```

---

## D. Feature & label provenance

### D1 · MEDIUM — ESM features silently zero-pad or truncate on length mismatch
`build_esm_features.py:126-133` — on `emb.shape[0] != len(res_list)` it pads with
zeros or truncates, with no warning, error or log. `build_graph_xl` only validates
the **row count**, which the pad has already forced to match. A real misalignment
of the 480 ESM dims is therefore unobservable end to end. Make it raise.

### D2 · MEDIUM — No provenance link between an ESM `.npy` and the graph `.pt`
Row count is the only tie. No sequence hash, no source-file checksum. Regenerating
`_clean.pdb` (different `strip_heteroatoms` keep-set) while a stale `.npy` remains
gives a silent misalignment of 480 of 520 feature dims whenever the residue count
coincidentally matches.

### D3 · MEDIUM — `build_graphs_xl.py` skips existing graphs without `--force`
Line 43 `already exists, skipping`. A graph directory can silently hold a mix of
pre-fix and post-fix graphs — precisely the state E006's rebuild creates.

### D4 · MEDIUM — `generate_labels.py` manifest hash is not reproducible
The docstring promises "a deterministic hash-verified label manifest", but
`generated_at: datetime.now().isoformat()` is inside the hashed record
(`scripts/generate_labels.py:371,386`), so every run produces different hashes for
identical inputs. The reproducibility guarantee the governance layer depends on
does not hold. Exclude timestamps from the hashed payload.

### D5 · MEDIUM — Chain taken from the first record, tokens unioned across all
`generate_labels.py:261` sets `apo_to_chain[apo] = records[0].get("apo_chain","A")`
while `apo_to_tokens[apo]` unions pocket tokens across **every** holo record. Tokens
belonging to a different apo chain can never match `present_auths` (filtered to the
single target chain) and silently become masked (`-1`), inflating `fraction_masked`
— which then feeds the 50% structure-exclusion threshold at line 250.

### D6 · LOW now / HIGH if enabled — Class-1 remap writes the un-remapped key
On a `label_seq_id` fallback (`generate_labels.py:193-201`) the positive is stored
under the **original** token; the resolved `auth_seq_id` goes only to the remap log.
`phase3_graphs/builder.py` aligns on auth-based `label_key`, so a remapped positive
either hard-fails alignment or — if that number happens to be another residue's
`auth_seq_id` — silently labels the **wrong residue**.
**Verified not currently triggered:** `data/registries/residue_remap_log.json`
reports `total_remaps: 0`. Fix before remapping is ever switched on.

### D7 · MEDIUM — Secondary structure fails silently
`parse_pdb._parse_secondary_structure` returns `{}` for any file without
HELIX/SHEET records, and every residue silently becomes coil — 3 of 40 feature
dims wrong with no signal. Inconsistent with the sibling SASA path, which was
given a warning in the BUG-024 partial fix. Give SS the same treatment.

---

## E. Scientific-definition issues (code-level, affect reported numbers)

### E1 · MEDIUM — Pretrain and fine-tune labels use different definitions
`label_pocket_residues` (`parse_pdb.py:195`) defines the PCNA ground truth by
**Cα**-within-6 Å, while CryptoBench/CryptoSite pretraining labels come from the
benchmark's own heavy-atom criterion. The model is pretrained on one label
definition and fine-tuned/evaluated on another. The docstring flags the Cα
approximation as a known limitation, but its effect on the headline numbers is
not quantified anywhere.

### E2 · MEDIUM — ESM2 embeddings are computed on gap-spliced sequences
`build_esm_features.embed_pdb` joins only the *observed* residues per chain, so
unresolved loops are concatenated out and ESM2 receives a sequence that does not
exist. Undocumented in the module or in LIMITATIONS.

### E3 · LOW-MEDIUM — Chain one-hot is positional, not identity-based
`graph_construction.py:211` builds `chain_to_idx` from `sorted(unique_chains)[:3]`,
so a structure with chains B/C/D maps B→`100`. The docstring claims
"A=100, B=010, C=001". Matters for cross-structure consistency and for the
BUG-022 leakage argument.

---

## F. Robustness & performance (low)

- **F1** `phase3_graphs/builder.py:320` hashes the graph by serialising every array
  to Python lists (`node_features.tolist()`, `edge_index.tolist()`) — for an
  O(N²)-edge graph this is a large, slow allocation. Hash the buffers instead.
- **F2** `phase3_data/graph_loader.py:55` loads `edge_distance` (which holds
  `np.inf` for sequential edges) into `edge_attr`. `GraphSAGE3L` ignores it today;
  any future edge-aware model silently ingests infinities.
- **F3** 48 broad `except Exception` / `except: pass` sites across `src` + `scripts`.
- **F4** `torch.load(..., weights_only=False)` in 8+ places (arbitrary-code path;
  acceptable for local artifacts, not for anything downloaded).
- **F5** `datetime.utcnow()` (`train.py:399`) is deprecated in Python 3.12+.

---

## G. Test coverage

22 tests over the 16.7k-LOC production tree, in 4 files
(`test_checkpoint_loading`, `test_graph_shape`, `test_label_alignment`,
`test_pocket_dynamics`). **None of findings B1–B6, C1–C2 or D1–D7 is covered** —
there is no test for the training loop, any loss function, metric aggregation,
split integrity, or ESM alignment. The governed tree's 93 tests are stronger but
leave `phase3_evaluation/metrics.py` untested for the degenerate class cases in C1.

Highest-value tests to add, in order:
1. `focal_loss` gradient magnitude on saturated inputs (B2)
2. `ranking_loss` invariance to residue permutation (B3)
3. `compute_metrics_from_lists` on all-positive / all-negative proteins (C1)
4. `--resume` with a nonexistent path must raise (B1)
5. ESM row-count mismatch must raise, not pad (D1)

---

## Suggested order of work

1. **B1** — one-line guard; it invalidates fine-tune provenance today.
2. **A1/A2** — merge `fix-pocket-dynamics` + `graph-leakage-fix`, then push to the
   public repo. It currently serves the buggy code under the project's name.
3. **B2, B3** — both change training dynamics; fix together and retrain once.
4. **C1, D4** — cheap, and both undermine numbers the governance layer certifies.
5. **A3** — decide explicitly whether `zero_chain_onehot=True` becomes the default,
   and record the ablation either way.
6. **D1/D2** — add a sequence hash to the ESM/graph handoff.
