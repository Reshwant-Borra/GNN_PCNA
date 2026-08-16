# Pre-MD GO Checklist

HISTORICAL / SUPERSEDED.

This checklist documents the older generic `cand_A_2026-08` pre-MD gate flow.
It is not the current execution runbook. Current source of truth is
`PROJECT_STATUS.md`; current practical commands are in
`md_validation_4070/FINAL_MD_EXECUTION_INSTRUCTIONS.md` and must use `./md.sh`.

The current frozen pocket is `final_consensus_1w60_20260815`; the current exact
next command is:

```bash
./md.sh smoke
```

Do not use the direct `python run_md.py ... cand_A_2026-08` examples below as
current instructions.

**Definition of GO used here:** we are ready to run the GNN over the PCNA structures, score
every residue, identify candidate pockets, and then use MD to test whether a candidate pocket
has *real dynamics* (does it transiently open?).

Every stage below has a **pass criterion**. A stage that fails is not a formality — each one
corresponds to a defect that was measured on this repo and that would silently produce a
wrong or uninterpretable answer. Do not skip forward.

Status of the code as of the 2026-08 pre-MD audit: all six *code* blockers are fixed and
regression-tested (`gnn_xl_worktree/tests/test_pre_md_release_gate.py`, 16 tests). What
remains is **Stage 3**, which is a scientific question, not a bug.

---

## Stage 0 — environment

```bash
cd <gnn worktree>
git rev-parse --abbrev-ref HEAD          # must print: graph-leakage-fix
python -m pytest tests/test_pre_md_release_gate.py -q -m "not slow"
```

**Pass:** branch is `graph-leakage-fix`; 15 passed (the 16th is `-m slow`, ~2 min, run it once).

The MD stage needs its own env: `conda env create -f md_validation_4070/environment.yml`.

---

## Stage 1 — data

```bash
python scripts/download_data.py
python scripts/build_esm_features.py      # downloads ESM2 (~1 GB) once
python scripts/build_graphs_xl.py
```

**Pass:** `data/raw`, `data/esm_features`, `data/graphs_xl` populated.

> Known, non-blocking: the committed graphs' secondary-structure node feature is dead
> (all-coil), and `data/pcna_xl/*.pt` are pre-BUG-020/021. Regenerating with the command
> above is what makes Stage 2 valid.

---

## Stage 2 — retrain, **at ≥ 3 seeds**

The virtual-node batch-mixing fix (`84c6aaa`) changed training semantics, and every
checkpoint predating it was trained while the virtual node averaged context across all 4
proteins in a batch. Inference now **refuses** such a checkpoint.

```bash
for s in 42 43 44; do
  python scripts/finetune_v3_fixed.py --seed $s --out checkpoints/seed_$s/best.ckpt
done
```

**Pass:** three checkpoints, each with a `best_meta.json` recording seed / epoch / sha256.

Optional but recommended — the script's own "KEY NEW METRIC" (apo false-positive rate) was
computed, printed, and then ignored by checkpoint selection. Enforce it:

```bash
python scripts/finetune_v3_fixed.py --seed 42 --max_apo_fp 5 --out checkpoints/seed_42/best.ckpt
```

> One seed is not a result. Two identical *unseeded* invocations previously produced two
> different checkpoints **and two different candidate pockets** (chain B / 35 residues vs
> chain A / 4 residues).

---

## Stage 3 — stability gate ← **THIS IS THE ONE THAT CURRENTLY BLOCKS GO**

```bash
cd md_validation_4070/gnn_pocket_search
python seed_stability.py \
    --worktree <gnn worktree> --pdb 1W60 \
    --ckpt <worktree>/checkpoints/seed_42/best.ckpt \
    --ckpt <worktree>/checkpoints/seed_43/best.ckpt \
    --ckpt <worktree>/checkpoints/seed_44/best.ckpt \
    --out stability_1W60.json --consensus-out consensus_1W60.json
```

**Pass:** `VERDICT: STABLE` — mean pairwise Jaccard ≥ 0.5, ≥ 8 residues at ≥ 60% agreement,
and at least one run whose top cluster beats its runner-up by ≥ 0.02 mean score.

**On UNSTABLE, do not proceed to MD.** The pocket would be a property of the seed, not of
the protein, and the MD result would be uninterpretable regardless of what it showed. Options,
in order of preference:

1. Train longer / to convergence and re-test — instability may be undertraining.
2. Raise the number of seeds to 5 and use the consensus if one emerges.
3. Fix the selection rule itself. Two measured causes:
   - ranking is by **mean** score and so is size-blind — 49 of 59 structures selected a
     3-residue "pocket";
   - `DBSCAN(eps=6.0)` exceeds PCNA's consecutive Cα–Cα spacing (measured 3.75–3.83 Å), so
     any contiguous above-threshold run merges into one cluster; one checkpoint produced a
     505/510-residue "pocket".
   A size-aware ranking (e.g. `mean × log n`) and a smaller `eps` are the obvious levers.
4. Accept a *known* site (AOH1996) as the MD target and report the novel-pocket arm as not
   yet supported.

**Reference measurement (2026-08-11, three 2-epoch checkpoints):** Jaccard **0.000**;
6 / 0 / 11 residues selected. That was a tool demonstration on deliberately short runs — it
is not a verdict on the real retrain, but it is the reason this gate exists.

---

## Stage 4 — pocket export

```bash
bash run_pocket_search.sh <worktree> 1W60 cand_A_2026-08 \
     <worktree>/.memory/PROJECT_STATE.md \
     <worktree>/checkpoints/seed_42/best.ckpt 8GLA
```

The checkpoint is now a **required** argument and is passed to both inference and the
provenance record, so the model that produced the pocket and the model named in the handoff
cannot diverge.

**Pass:** reaches `[3/3]`, writes `cand_A_2026-08_handoff.json`, and clears the plausibility
guards in `export_handoff.sanity_check_cluster`:

| guard | threshold | why |
|---|---|---|
| size | 8 ≤ n ≤ 60 residues | ranking is size-blind |
| chain fraction | ≤ 25% of a chain | DBSCAN eps merges pocket into backbone |
| runner-up margin | ≥ 0.02 mean score | candidate must be determined by the model |

Then **manually confirm** `pocket_residues` is a list of `{chain, resid}` pairs. The AOH-class
site spans two subunits, so a bare residue number is ambiguous across the homotrimer.

A recorded GATE-6 approval is required and must be written by the accountable human — the
export tool refuses without one, and refuses governance-override text.

---

## Stage 5 — MD preparation smoke test

```bash
cd <repo-root>
./md.sh smoke
```

**Pass:** prep prints the biological assembly with **exactly 3 PCNA chains**, a non-zero
`internal_missing_residues_rebuilt` for 8GLA (~50), and no fatal from
`assert_no_impossible_bonds`.

> This is the arm that was most broken. 8GLA previously prepared with **13 covalent bonds up
> to 10.79 Å** (r₀ = 1.33 Å; one worth 183,222 kJ/mol) fused across unresolved loops, because
> the structure was written without SEQRES so PDBFixer never saw the gaps. Fixed at the root
> (SEQRES transfer) with a hard assertion as backstop — verified 13 → **0**.

---

## Stage 6 — MD production

```bash
./md.sh production
```

Production is blocked unless smoke, control-first validation, Gate-6 approval,
CUDA enforcement, and `md_workflow.py production-gate` all pass. Direct
production-scale `run_md.py` commands are not supported.

---

## Stage 7 — analysis and the positive-control gate

```bash
./md.sh analyze
```

**Pass:** `[parity]` reports apo and control measured over an **identical atom count**, and
the positive control passes (`control_pocket_sasa > apo`, |d| > 0.5, per-replicate consistent).

Two corrections now applied here, both measured:

- **Atom-level parity.** Apo and control resolved the same 56 residues but **854 vs 855
  atoms** (a terminal `OXT`). SASA is per-atom, so a residue-level check was not enough.
- **Terminus/gap exclusion.** Residue 254 was internal in apo but a chain end in the control
  — worth **+1.496 nm²** from terminus status alone, against **+0.435 nm²** of genuine
  structural difference across the other 22 residues. Differencing those measures where the
  crystal stopped, not whether the pocket opened. Override with `--keep-termini` only if you
  state the caveat.

If the control fails, the honest report is **"the method cannot see opening here"** — not
"the pocket does not open".

---

## What GO does *not* certify

- Held-out generalization numbers. The committed paper artifact reports a
  homology-contaminated AUROC 0.8081 / AUPRC 0.3441 as an "independent held-out" estimate,
  contradicting the repo's own homology screen. Use the homology-clean figures.
- Novelty. Overlap classification requires the doc-12 audit; `classification=
  not_in_any_known_region` is not a novelty claim.
- 1W60 as an interface site. The pinned identification structure has **0 cross-chain graph
  edges**, so a pocket found on it is not, on that evidence, a two-subunit interface pocket.

---

*Generated from the 2026-08 pre-MD release audit: 8 investigation streams + 8 adversarial
refutation passes; 78 findings survived refutation (6 confirmed active bugs, 15 false
positives killed). Regression tests: `gnn_xl_worktree/tests/test_pre_md_release_gate.py`.*
