# GNN-PCNA — Assessment of the Failed Validation Attempt
### Why the last cycle stalled and why the predicted pocket "came back with no dynamics"

**Project:** GNN-based cryptic-pocket prediction on human PCNA (Proliferating Cell Nuclear Antigen)
**Repository:** `Reshwant-Borra/GNN_PCNA` (local: `C:/Users/advay/GNN_PNCA/`)
**Authors of the work:** Advay (validation / MD / audit track) · Reshwant Borra (model / training / evaluation)
**This document:** internal post-mortem + handoff, compiled 2026-07-23
**Status of the scientific claim:** *unproven — not disproven.* The one MD test run to date was
methodologically invalid, so it neither supports nor refutes the cryptic-pocket hypothesis.

---

## 0. How to read this document

This is an honest failure analysis, written to be handed to an outside reviewer (human or an AI
research agent) so they can pick up the project without re-deriving the history. It separates three
things that are easy to conflate:

1. **What was observed** — the predicted pocket showed essentially no motion in molecular dynamics (MD).
2. **What that observation means** — *nothing yet*, because the test could not have detected motion even
   if it were there.
3. **Why the project stalled** — a stack of MD-design defects, a structural bug, and a reproducibility
   gap that together make the current results un-defensible in front of a reviewer.

The single most important sentence: **a negative that a test was incapable of turning positive is not a
negative — it is an uninterpretable test.** Everything below is the evidence for that statement and the
plan to run the test correctly.

---

## 1. Executive summary

- **Goal.** Predict a *cryptic* (transient, ligand-inducible) druggable pocket on PCNA — a cancer target
  overexpressed in breast, colorectal, and lung tumors — using a graph neural network (GNN), then
  confirm the pocket is genuinely dynamic with MD.
- **The model works and reproduces.** On local CPU the GNN reproduces its recorded numbers exactly:
  AOH1996 positive-control gate mean score **0.8676** (top residue **#1 of 952**, PASS), held-out
  generalization **AUROC 0.8081 / AUPRC 0.3441** across 13 independent CryptoSite proteins (**6.2×**
  above the trivial baseline AUPRC of 0.0557). The failure is **not** in the neural network.
- **The scientific weight rests on MD, and the MD was invalid.** The GNN reliably says *where* a pocket
  is (it localizes the AOH1996 site even from the closed apo structure) but gives **no signal that the
  site opens** — at matched pocket residues it scores the site ~0.87 in holo (8GLA) and ~0.91 in apo
  (1W60), a per-residue holo−apo difference of ≈ **−0.04** (essentially zero). So the *"cryptic /
  dynamic"* half of the claim can only come from MD. It never validly did.
- **What "came back with no dynamics" actually was.** A single 25 ns simulation of the **wrong apo
  structure** (1AXC, a p21-bound complex), analyzing the **wrong residues** (arbitrary "novel windows,"
  not the validated pocket), with **no positive control**, only **n = 1** usable replicate, and an
  analysis that was **numerically corrupt** (it initially reported a physically impossible 25 Å RMSD).
  The corrected numbers showed the candidate windows were the *most rigid* regions in the protein —
  but this test was structurally incapable of showing anything else.
- **Additional structural bug.** Even the "true apo vs. holo control" comparison, as first built, was
  **apples-to-oranges**: the pipeline simulated the deposited *crystallographic asymmetric unit* instead
  of the *biological homotrimer*, so the apo and control systems were different molecular assemblies and
  the pocket's subunit interface didn't even exist in the apo box.
- **Reproducibility gap.** The exact model that produced the headline numbers currently exists **only as
  compiled `.pyc` bytecode**, with no readable source, no committed checkpoint, and a missing inference
  driver. A reviewer cannot re-run it. This is the thing most likely to sink the project on submission,
  independent of the biology.
- **All of the above is now fixed in a rebuilt validation package** (`md_validation_4070/` v2) that has a
  built-in positive control and an automatic gate that reports **"inconclusive," never a false
  "negative."** The corrected test has not yet been run on GPU.

**Bottom line:** the project did not fail scientifically. It failed *procedurally* — the validation
experiment was underpowered and mis-specified, and the result chain is not yet reproducible. Both are
fixable, and most of the fixes are already built.

---

## 2. The project in one page

**Biology.** PCNA is the DNA-replication sliding clamp — a ring-shaped homotrimer that encircles DNA and
is essential for replication and repair. It is overexpressed in many cancers, which makes it an
attractive but historically "undruggable" target: most of its surface is flat protein–protein interface
(the PIP-box front face, the interdomain connecting loop / IDCL). The exciting recent development is
**AOH1996** (the small molecule with ligand code **ZQZ**, co-crystallized with PCNA in **PDB 8GLA**;
PMID 37531956), which binds at a **two-subunit interface pocket** and reached clinical testing — evidence
that a targetable pocket exists on this "undruggable" protein.

**Hypothesis.** If one druggable interface pocket exists on PCNA, a model trained to recognize
cryptic-pocket signatures might find *others* (or confirm the AOH1996 site) — and MD can show whether
such a site is genuinely dynamic/cryptic rather than a static crystallographic accident.

**Method.**
- **Model:** a dual-branch graph neural network, **PocketGNNXL** (~13.4 M parameters). Node features are
  520-dimensional: 40 hand-crafted features plus a 480-dim ESM2 protein-language-model embedding
  (`esm2_t12_35M_UR50D`). Spatial (8 Å contact) and sequential edges, GATv2 attention, a virtual node
  for global context. It scores every residue for pocket-lining probability.
- **Ground truth:** the AOH1996 pocket in 8GLA (the ZQZ contact shell) as a *known* positive; apo PCNA
  (**1W60**) as the closed-state baseline.
- **Validation logic:** GNN localizes candidate pockets → MD tests whether they open → only a
  positive-controlled, adequately sampled MD can license a "cryptic pocket" claim.

**Governance.** The project runs under an unusually strict internal rulebook
(`docs/scientific_governance/`, 40 binding documents). Doc 13 (MD Validation Rules) states plainly that
*"treating no pocket opening as failed MD"* is a **forbidden action**, that a single 100 ns trajectory is
**exploratory**, that **negative results are valid**, and that **enhanced sampling may be needed for
cryptic pockets.** The failure analyzed here is, in part, a failure to have followed the project's own
rules on the first attempt.

---

## 3. What was actually observed — "the pocket came back with no dynamics"

The only production MD executed before this cycle was on **PDB 1AXC**, 25 ns, on a rented GPU
(RunPod B200), analyzed 2026-05-30 (`outputs/phase5_md/PHASE5_MD_RESULTS.md`). After the analysis was
re-run to fix a numerical corruption (see §5, M6), the corrected findings were:

**Simulation was stable** (so the "rigidity" is not a broken run): backbone Cα RMSD mean **0.255 nm**,
max **0.305 nm**; potential energy flat (~−2.68M kJ/mol), 300 K, 1.01 g/mL.

**Per-window Cα flexibility (RMSF), the core "no dynamics" result:**

| Window   | Role                          | RMSF (nm) | vs. reference |
|----------|-------------------------------|-----------|---------------|
| 239–243  | GNN novel candidate A         | 0.081     | 0.65×         |
| 28–32    | GNN novel candidate B         | 0.081     | 0.65×         |
| 206–210  | GNN novel candidate C         | 0.074     | 0.59×         |
| 134–138  | IDCL-adjacent control         | 0.084     | 0.67×         |
| 118–122  | IDCL/PIP reference (=1.00×)    | 0.126     | 1.00×         |

The GNN's candidate windows were **the most rigid regions measured** — ~0.59–0.65× as mobile as an
already-modest reference loop. Pocket-opening proxies agreed: **no sustained opening in any monomer**;
only transient solvent-exposure (SASA) excursions of ~18–26% lasting **2–7 of 200 frames** with ~zero
second-half drift (i.e. jitter that returns to baseline). The only sustained widening was in **134–138**,
the *known-flexible* IDCL loop — expected motion, not a discovery.

**The project's own result statement (2026-05-30) was already honest about this:**
> *"the GNN-predicted novel candidate pockets (239–243, 28–32, 206–210) remained rigid and did not open …
> This is a valid negative/inconclusive result — not falsification: 25 ns / n = 1 / no positive control
> cannot sample ns–µs cryptic-opening events. No druggability, validated-site, or novel-site claims are
> supported."*
> (`result_class: negative_inconclusive`)

So "the pocket came back with no dynamics" is literally true for what was measured — **but what was
measured was the wrong experiment.** §§4–5 explain why.

---

## 4. The central finding: this was an invalid test, not negative biology

Cryptic-pocket opening is a **rare, slow event** — it happens on nanosecond-to-microsecond (and often
longer) timescales, frequently only under a ligand or cosolvent perturbation. Detecting it requires (a)
starting from the correct closed state, (b) proving your method *can* see opening when it is really there
(a positive control), (c) measuring the *right* residues, and (d) enough sampling for a rare event to
occur. The 1AXC run satisfied **none** of these. Concretely:

> A test that cannot produce a positive result even when the phenomenon is present cannot produce an
> interpretable negative. Under the project's `13_MD_VALIDATION_RULES.md`, a negative MD is a valid
> result **only if the test was capable of producing a positive.** The 1AXC run was not, so its correct
> classification is **inconclusive / underpowered**, not negative.

This is not a rationalization to rescue a hypothesis. It is the difference between "we looked and it
isn't there" and "we didn't actually look." The 1AXC run is the second.

---

## 5. Root cause A — the MD experiment was mis-designed and mis-executed

Six stacked defects (M1–M6), each independently sufficient to invalidate the negative, plus a seventh
structural bug found later. Every one is now fixed in the v2 package (§8).

| # | Defect | Why it invalidates the "negative" |
|---|--------|-----------------------------------|
| **M1** | **Wrong apo state.** 1AXC is the PCNA–**p21** PIP-box complex (Gulbis 1996, PMID 8861913); the run deleted the peptide and simulated "apo-from-p21." An earlier draft even mislabeled **5E0V** as the apo reference — but 5E0V is the **S228I disease mutant + FEN1 peptide** (Duffy 2016, PMID 26688547), not apo WT. | You are relaxing *away from* a bound conformation, not sampling the true closed apo ensemble. Wrong starting state → wrong dynamics. True apo is **1W60**. |
| **M2** | **No positive control.** The known-open AOH1996 pocket (holo 8GLA) was never simulated. | Without demonstrating the method detects the *known* open pocket, "no opening" is unfalsifiable — it could mean "no pocket" or "blind method." |
| **M3** | **Measured the wrong residues.** Analysis targeted arbitrary "novel windows" (239–243, 206–210, 28–32) rather than the validated AOH1996 pocket residues. | The claim is about a specific site; the test looked elsewhere. |
| **M4** | **n = 1, ~20–25 ns usable.** Replicate 2 died at the budget wall (41 frames); replicate 3 never ran. | Cryptic opening is a ns–µs rare event; a single ~20 ns trajectory essentially never samples it. Absence of opening ≠ evidence of no pocket. |
| **M5** | **Solvated topology not saved** with the trajectory. | Downstream pocket-volume analysis (and the paper's MD figures) were blocked; results not re-analyzable. |
| **M6** | **Numerically corrupt analysis.** The original report showed RMSD **2.468 nm (~25 Å)** and RMSF 1–3 nm — physically impossible for a stable fold. Root causes (adversarially confirmed): **RMSF computed about frame 0 instead of the mean position**, and **no periodic-boundary (PBC) imaging before superposition**, so a molecule wrapping across the box registers as a ~7–10 nm "jump." | The headline metrics were garbage until re-run with `image_molecules()` + RMSF-about-mean. Any conclusion drawn before that correction is void. |

**The seventh (structural) bug — apples-to-oranges apo vs. control.** When the "correct" comparison
(true apo 1W60 vs. holo control 8GLA) was first built, the code fetched each PDB's *deposited
asymmetric unit* via `PDBFixer(pdbid=…)` rather than reconstructing the **biological assembly**. PCNA's
functional unit is a **homotrimer ring**; the AOH1996 pocket only exists at a *genuine* subunit
interface. But 1W60's asymmetric unit is **2 chains that seed two different crystallographic trimers**
(their contact is a crystal-packing artifact, not the ring interface), while 8GLA's is **4 chains**. So
the positive-control gate was comparing **non-comparable molecular systems**, and in the apo box the
pocket's interface was not even physically present. (Fixed in v2 by rebuilding the biological homotrimer
with `gemmi.make_assembly` for both structures, hard-failing unless exactly 3 PCNA chains are produced.)

**Confirmed supporting code defects** (adversarially verified in a multi-agent audit; `file:line` cited
against source at audit time — spot-check before acting):

- **C1** `phase5_analyze_1axc_md.py:123-127` — RMSF about frame 0, not the mean (inflates flexibility).
- **C2** `phase5_analyze_1axc_md.py:82,95-101` — no PBC imaging before superposition (the 25 Å artifact).
- **C3** MonteCarloBarostat active during the nominal "NVT" phase (equilibration was silently NPT).
- **C4** three monomers in one box treated as "informal triplicates" — **pseudoreplication** (correlated,
  not independent; inflates apparent confidence).
- **C5** `fetch_structures.py` — 8GLA (3.77 Å) silently bypasses the 3.5 Å resolution hard-fail via a
  `PCNA_CORE_IDS` allowlist (the positive control is below the pipeline's own quality bar).
- **C6** `fetch_structures.py:138-140` — **chain-count validation is advertised in the docstring but never
  enforced.** This is the structural gap behind the recurring wrong-chain bugs (1AXC / 9B8T class).

---

## 6. Root cause B — the model localizes the pocket but cannot demonstrate it is dynamic

This is the deep reason the whole scientific weight fell on MD, and therefore the reason the invalid MD
was fatal to the cycle rather than a minor setback.

On re-running the model at **matched pocket residues**:

- Holo (8GLA) AOH1996 pocket mean score: **0.868**
- Apo (1W60) **same-residue** mean score: **0.907**
- Per-residue holo − apo difference: **≈ −0.04** (essentially zero, marginally *apo*-favoring)

The recorded discriminator `disc_score = 0.741` is **not** an apo↔holo contrast. It is
`mean(holo pocket) − mean(all apo residues = 0.127)` — a **foreground-vs-background** score (pocket vs.
the rest of the protein). It measures *"the model concentrates its signal on this site,"* which is true
and useful, **not** *"the model sees this site change between the closed and open states."*

**Implication.** The GNN is a good pocket **localizer** — it flags the AOH1996 site even from the closed
apo structure, and generalizes to held-out proteins (AUROC 0.8081). But it carries **no intrinsic
opening/dynamics signal**. So the "cryptic" (i.e. *dynamic*) part of the thesis is not something the
network can establish on its own — it must be shown physically, by MD. That places the entire burden of
the central claim on the MD experiment, which is exactly the experiment that was invalid. The two failure
modes compound: a claim that structurally depends on MD, resting on an MD run that could not test it.

*(An orthogonal, non-MD flexibility estimate — an Anisotropic Network Model / normal-mode analysis —
does point the right way: the AOH1996 pocket's fold-change flexibility is **0.857 in apo (sub-global,
closed)** vs. **1.157 in holo (above-global, ligand-associated)**, Δ = **+0.300**, with the internal
dynamic cross-correlation rising 0.0995 → 0.2093. This is **suggestive** that the site is
ligand-associated/flexible, but ANM is a coarse harmonic approximation, not conformational sampling — it
cannot substitute for a positive-controlled MD, and it should be reported as supporting context only.)*

---

## 7. Root cause C — the reproducibility / auditability gap (the biggest submission risk)

Independent of the biology, the result chain is currently **not reproducible from source**, which is the
first thing any competition judge, journal reviewer, or collaborator will check.

- **The headline model is `.pyc`-only.** The 520-dim dual-branch ESM2 `PocketGNNXL` that produced the
  reported metrics exists **only as compiled `.cpython-312.pyc` bytecode** — model, loss, training,
  scoring, and graph construction have **zero readable `.py`** in the legacy `src/` tree. Its loss
  function, class-imbalance handling, and AUPRC computation are therefore un-reviewable.
- **The inference driver is missing.** The orchestrator calls `scripts/bulk_inference.py`, which **does
  not exist**; the real score-producing step `run_v3_inference.py` is `.pyc`-only. `score_pockets` is
  pure post-processing (DBSCAN + AUROC on *precomputed* scores) and does not run the model.
- **No checkpoint is committed.** The referenced `checkpoints/pcna_reproduced/best.ckpt` /
  `best_meta.json` and **all** model weights are absent from the repo.
- **Two mutually incompatible pipelines.** The only *readable* model is a different, simpler one — a
  25-dim single-branch GraphSAGE with ESM explicitly excluded, marked dry-run-only, whose validation
  numbers are much lower (~0.65 AUROC / ~0.19 AUPRC). Feeding its 25-dim ESM-free graphs into the model
  that expects 520-dim ESM2 inputs is a hard dimension mismatch — so "reproducing from the readable code"
  silently reproduces the *wrong* model.
- **The score → residue mapping is unverifiable.** Array-index → PDB author residue number → UniProt
  P12004 numbering is done in compiled code plus hand-entered residue lists; an `auth_seq_id` vs.
  `label_seq_id` off-by-one, or a chain misassignment, would silently shift which residues are reported
  as "the pocket," and nothing readable checks it.

**What closing this requires before any submission:** restore readable `.py` source for the model, loss,
training, scoring, and inference that produced the reported numbers; commit the checkpoint and its
metadata; state, *per number*, exactly which model / features / split produced it; and add a written test
for the residue-numbering path. **A subsequently discovered training bug makes the retrain non-optional:**
the XL virtual-node used a global mean over *all* nodes in a batch, so at batch size > 1 one protein's
global-context node saw other proteins' residues. It is fixed (per-graph pooling), but **the old
checkpoint predates the fix and is stale — the model must be retrained before any number is quoted as a
result.**

---

## 8. What has already been fixed — the v2 validation package

All of §5 and the structural bug are remediated in **`md_validation_4070/`** (shipped as
`md_validation_4070_v2.zip`; also handed to the collaborator running GPU compute). It is a self-contained
OpenMM package whose *design goal is that it cannot return a false negative.*

- **True apo + true holo positive control.** Simulates **1W60** (closed apo, "does it open?") and **8GLA**
  (ligand ZQZ stripped, pocket starts open — the positive control).
- **Automatic positive-control gate.** `analyze_md.py` measures whether the openness metric reads larger
  for the open control (8GLA) than the closed apo (1W60). If it **cannot** separate them, the report
  prints **`Interpretable: False → inconclusive`** and explicitly instructs *"do NOT report this as 'no
  pocket'"* — the machinery that converts a would-be false negative into an honest "extend sampling."
- **Correct assembly.** Both structures are rebuilt into the **biological homotrimer** (gemmi crystal
  symmetry); the run **hard-fails** unless exactly 3 PCNA chains (~255 aa each) are produced; peptides
  (p21/FEN1) are dropped by length. Smoke-tested locally: 1W60 → 3 chains, 8GLA → 3 chains, **all 28
  pocket residues present on both interface chains, 0 fabricated**, AMBER14 parameterizes both.
- **Correct, reproducible pocket definition.** Residues come from `pockets/aoh1996.json` — a derived list
  (PCNA heavy-atom ≤ 4.5 Å to ligand ZQZ in 8GLA, 28 residues across the two interface chains), replacing
  the old hand-curated list that had dropped the IDCL contacts 121/124/129/131. New pockets are validated
  by dropping in a new JSON, so the anti-false-negative machinery carries over to any future GNN candidate.
- **Correct analysis.** PBC imaging *before* superposition, alignment on a pocket-excluded core (no
  circularity), RMSF about the mean, a frame-to-frame jump detector for genuine box-hop artifacts, and
  low-resolution/rebuilt-residue caveats (8GLA is 3.77 Å) surfaced next to every PASS/FAIL.
- **Adequate, resumable sampling.** Default **3 × 100 ns per structure**, HMR + 4 fs, checkpoint-resumable
  across reboots (`run_in_tmux.sh`), topology (`system_solvated.pdb`) saved next to every trajectory.

**What has not happened yet:** this corrected experiment has not been run on GPU. That run — control
first, then apo, then the gated analysis — is the gate that determines whether PCNA's predicted site is
actually cryptic, is static, or needs enhanced sampling to tell.

---

## 9. The honest interpretation, and what may and may not be claimed today

**May be stated now:**
- The GNN is a competent **pocket localizer** with reproducible held-out generalization (AUROC 0.8081)
  and clean recovery of the known AOH1996 site.
- The first MD cycle produced **no interpretable dynamics result**; it is best described as *inconclusive
  / underpowered*, and the reasons are fully characterized and fixed.
- Coarse normal-mode (ANM) analysis is **suggestive** that the AOH1996 site is more flexible in the
  ligand-associated state, but this is supporting context, not proof of a cryptic mechanism.

**May not be stated (yet):**
- That any PCNA site — the AOH1996 pocket or a novel one — has been **shown to be dynamic/cryptic by MD.**
- That the GNN's **novel** candidate windows are real pockets (the audit notes some abut known p21/PIP
  contacts, so "novel" itself needs the PCNA-specific overlap review before the word is used).
- Any **druggability or therapeutic** claim from computation alone.

**The one thing that would actually be fatal** — and which the project has deliberately guarded against —
is tuning the MD or its analysis to a predetermined favorable answer. The v2 gate is built to report the
truth in either direction; a reviewer who found a harness rigged toward a conclusion would end the
project, whereas an honestly reported negative is, by the project's own `30_NEGATIVE_RESULT_SUCCESS_
CRITERIA.md`, a valid result.

---

## 10. Path forward (what the corrected cycle looks like)

1. **Rebuild for reproducibility (blocking for any submission):** restore readable source + commit the
   checkpoint, **retrain after the virtual-node fix**, and attach each reported number to a specific
   model/features/split. (§7)
2. **Run the positive-controlled MD (v2 package):** 8GLA control first, then 1W60 apo, then the gated
   analysis. Read the **Interpretable** line before reading anything else. (§8)
3. **If the gate reads `Interpretable: False`,** the unbiased 100 ns run cannot see opening → escalate to
   **enhanced sampling** (e.g. metadynamics / cosolvent (mixed-solvent) MD / accelerated MD on a
   pocket-opening collective variable), where "it does not open" remains a permitted answer.
4. **Triangulate with orthogonal methods** rather than resting on the GNN alone (cryptic-site predictors,
   pocket-detection on the trajectory, fragment/hotspot mapping) — see the companion prompt for
   Claude for Life Sciences.
5. **Report whatever it shows, honestly** — a confirmed cryptic site, a static site, or "needs longer
   sampling" are all publishable outcomes under the project's governance.

---

## Appendix A — Key numbers (verified against source)

| Quantity | Value | Source |
|---|---|---|
| GNN AOH1996 gate mean score | 0.8676 (top #1/952, PASS) | `RERUN_EVIDENCE.md`, `INCIDENT_REPORT.md` §C |
| Held-out generalization | AUROC 0.8081 / AUPRC 0.3441 (13 proteins) | `RERUN_EVIDENCE.md` |
| Trivial baseline AUPRC / lift | 0.0557 / 6.2× | `project-gnn-pcna` record |
| Per-residue holo−apo (matched pocket) | ≈ −0.04 (holo 0.868 / apo 0.907) | `RERUN_EVIDENCE.md` §3 |
| `disc_score` (foreground−background) | 0.741 = mean(holo pocket) − mean(all apo = 0.127) | `INCIDENT_REPORT.md` §C |
| ANM flexibility fold-change apo / holo / Δ | 0.857 / 1.157 / +0.300 | `project-gnn-pcna` (corrected) |
| 1AXC MD candidate-window RMSF (nm) | 0.081 / 0.081 / 0.074 (0.59–0.65× ref) | `PHASE5_MD_RESULTS.md` |
| 1AXC MD backbone RMSD (stable) | mean 0.255 nm / max 0.305 nm | `PHASE5_MD_RESULTS.md` |
| Corrupt original RMSD (pre-fix) | 2.468 nm (~25 Å) | `PHASE5_MD_RESULTS.md`, `INCIDENT_REPORT.md` M6 |
| v2 pocket definition | 28 residues, PCNA heavy-atom ≤4.5 Å to ZQZ (8GLA) | `pockets/aoh1996.json` |

## Appendix B — Structures referenced

| PDB | Identity | Role |
|---|---|---|
| **8GLA** | PCNA + AOH1996 (ligand **ZQZ**), 3.77 Å; PMID 37531956 | Holo ground truth / MD positive control |
| **1W60** | Apo wild-type human PCNA homotrimer | True closed-state apo (correct MD reference) |
| **1AXC** | PCNA–p21 PIP-box complex; PMID 8861913 | The *incorrect* apo used in the failed MD |
| **5E0V** | PCNA **S228I** variant + FEN1 peptide; PMID 26688547 | Mislabeled "apo" in an early draft — it is not |
| **9B8T** | PCNA + DNA polymerase ε | Chain-assignment bug: chain A = pol ε, B/C/D = PCNA |

## Appendix C — Glossary

- **Cryptic pocket** — a druggable cavity absent (or closed) in the apo/unbound structure that opens
  transiently, typically only detectable in dynamics or upon ligand/cosolvent perturbation.
- **Apo / holo** — unbound (closed) vs. ligand-bound (open) protein state.
- **RMSD / RMSF** — root-mean-square deviation (whole-structure drift over time) / fluctuation
  (per-residue mobility about its mean). Low RMSF = rigid.
- **PBC imaging** — reconstructing molecules that wrap across the periodic simulation box before
  measuring geometry; skipping it produces spurious huge RMSD/RMSF.
- **Positive control (here)** — simulating the known-open pocket (8GLA) to prove the method can detect
  opening; without it a "no opening" reading is uninterpretable.
- **ANM / normal-mode analysis** — a coarse elastic-network estimate of intrinsic flexibility; cheap,
  suggestive, not a substitute for MD sampling.
- **ESM2** — a protein language model; its per-residue embeddings are half the GNN's input features.
- **AUROC / AUPRC** — ranking-quality metrics; AUPRC is the honest one for a rare positive class (pocket
  residues are a small fraction of all residues).

---

*Prepared as an internal post-mortem for the GNN-PCNA project. Numbers are transcribed from the repo's
own reports and were re-verified against source files. Where a claim cites `file:line`, it reflects the
source at audit time and should be spot-checked before it is acted on.*
