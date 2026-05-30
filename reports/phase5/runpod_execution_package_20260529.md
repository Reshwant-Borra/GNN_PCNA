# RunPod Execution Package - Budget-Constrained Time-Crunch MD

**Date:** 2026-05-29  
**Status:** APPROVED WITH MODIFICATIONS - execution package only  
**Scope:** RunPod-ready instructions for exploratory short-timescale MD.  
**No MD has been launched by this package.**

**Final recommendation:** APPROVE WITH MODIFICATIONS. Execute only the 3 x 25 ns
budget-constrained plan if the RunPod console price and startup time keep the run inside
the $30 hard cap with the safety margin below.

---

## Scientific Scope

### Exact system

| Field | Value |
|---|---|
| System ID | `phase5_time_crunch_1axc_3x25ns` |
| Starting structure | PDB `1AXC` |
| Prepared state | apo-from-p21 PCNA trimer |
| Retained chains | PCNA chains `A`, `C`, `E` |
| Removed chains | p21 peptide chains and any non-retained chains |
| Replicates | 3 |
| Production length | 25 ns per replicate |
| Total planned sampling | 75 ns |
| Force field | OpenMM `amber19-all.xml` protein parameters, `amber14/tip3p.xml` water |
| Water/ions | TIP3P, neutralized, 0.15 M ionic strength |
| Protonation | pH 7.4 hydrogens during PDBFixer preparation |

### Candidate windows analyzed

- Tier 1A: `239-243`
- Tier 1A: `28-32`
- Tier 1A: `206-210`
- Tier 2 control: `134-138`
- Optional read-only internal reference: `118-122`

The `118-122` reference is not the official 8GLA/AOH1996 positive-control MD system.
It is only a no-extra-cost IDCL/front-face reference extracted from the same 1AXC
trajectories.

### Deferred systems

- `8GLA` holo with ZQZ retained.
- `8GLA` apo-from-holo with ZQZ removed.
- Official AOH1996/8GLA positive-control MD.
- Tier 1B trimer-interface candidates: `170-174`, `175-179`, `152-156`.
- Any expanded or enhanced-sampling MD campaign.

### Expected limitations

This is short-timescale exploratory MD, not official GATE 7 Wave 1 completion. The run
can show early local stability/flexibility trends under a 1AXC apo-from-p21 setup. It
cannot validate a binding site, prove pocket opening, establish druggability, support
therapeutic claims, or replace the deferred 8GLA positive-control systems.

Allowed wording after successful analysis is limited to statements like:

> "Short-timescale exploratory MD of 1AXC apo-from-p21 was performed. Under this
> limited 25 ns replicate setup, the specified windows showed/did not show early local
> flexibility or geometry changes. Results are hypothesis-generating and require
> longer MD and the deferred 8GLA positive-control systems."

---

## RunPod Hardware Recommendation

### Budget

| Item | Value |
|---|---:|
| Hard maximum spend | $30 |
| Planning B200 cost | ~$6/hour |
| Target spend | $21-$27 |
| Safety reserve | 20-30% of budget/time |
| Hard stop | Terminate before projected spend exceeds $30 |

Current RunPod public GPU listings should be checked immediately before launch. At
planning time, RunPod lists B200 at about `$5.89/hr` with 180 GB VRAM, 283 GB RAM, and
28 vCPUs. Pricing is operationally unstable, so the console price at launch controls.

### Recommended pod

| Resource | Recommendation |
|---|---|
| GPU | 1 x B200 Secure Cloud preferred |
| Fallback GPU | 1 x H200; then 1 x H100 SXM/NVL if B200/H200 unavailable |
| Minimum VRAM | 80 GB usable; B200 180 GB preferred |
| CPU | Use included B200 allocation; 28 vCPUs preferred |
| RAM | Use included B200 allocation; 283 GB preferred |
| Disk | 100 GB minimum; 200 GB preferred |
| Operating system | Ubuntu Linux CUDA 12.x container |
| Template/image | RunPod PyTorch CUDA 12.x image or equivalent CUDA-devel image with conda |

### Estimated storage usage

For `3 x 25 ns` with 100 ps DCD frames:

- Prepared inputs and logs: <1 GB.
- Trajectories: ~0.5-2 GB per replicate, system-size dependent.
- Checkpoints/final PDB/state CSV/plots: ~1-5 GB total.
- Recommended storage allocation: 100 GB minimum, 200 GB preferred for safety.

### Estimated runtime

| Case | Runtime | Cost at $6/hr | Notes |
|---|---:|---:|---|
| Best case | 2.0-3.0 h | $12-$18 | Smooth setup, high B200 throughput |
| Expected | 3.0-4.5 h | $18-$27 | Fits target if setup is efficient |
| Worst acceptable | 4.5-5.0 h | $27-$30 | Must stop before crossing hard cap |
| Overrun | >5.0 h | >$30 | Not allowed |

---

## RunPod Pod Specifications

Select:

- Cloud type: **Secure Cloud** if available.
- GPU: **B200**.
- GPU count: **1**.
- Container image/template: **RunPod PyTorch CUDA 12.x** image with conda/mamba support.
- Container disk: **50 GB minimum**.
- Volume/network disk: **100 GB minimum**, **200 GB preferred**.
- Expose HTTP/Jupyter only if needed; SSH is sufficient.
- Stop/terminate behavior: do not leave the pod idle after analysis. Download outputs
  and terminate immediately.

Fallback:

1. If no B200 is available, choose H200 with the same disk limits.
2. If H200 is unavailable, choose H100 SXM/NVL only if the listed hourly price still
   allows at least 3.5 hours under the $30 cap.
3. Do not start on a slow or unverified GPU if the console estimate makes `3 x 25 ns`
   impossible inside the target spend.

---

## Environment Setup

### Version requirements

| Component | Requirement |
|---|---|
| Python | 3.11 |
| OpenMM | 8.2.x |
| CUDA | CUDA 12.x image with visible NVIDIA GPU and OpenMM CUDA platform |
| Structure prep | PDBFixer |
| Analysis | MDTraj, MDAnalysis, NumPy, pandas, matplotlib |
| Environment file | `envs/phase5_md_runpod.yml` |

The conda environment installs:

- `python=3.11`
- `openmm=8.2.*`
- `pdbfixer`
- `mdtraj`
- `mdanalysis`
- `numpy`
- `pandas`
- `matplotlib`
- `tqdm`
- `pyyaml`

### Fresh RunPod commands

```bash
git clone <repo-url> GNN_PCNA
cd GNN_PCNA

conda env create -f envs/phase5_md_runpod.yml
conda activate phase5-md

python -m openmm.testInstallation
python scripts/phase5_run_1axc_openmm.py --help
python scripts/phase5_analyze_1axc_md.py --help
```

If `python -m openmm.testInstallation` does not show CUDA support, stop and fix the
container before starting production.

### Cloud smoke test

Run this before the paid production run:

```bash
python scripts/phase5_run_1axc_openmm.py \
  --output-root outputs/phase5_md/time_crunch_1axc_25ns \
  --smoke-test \
  --max-wall-hours 0.5 \
  --target-cost-usd 3 \
  --hard-cost-usd 5
```

Then check:

```bash
python scripts/phase5_analyze_1axc_md.py \
  --run-root outputs/phase5_md/time_crunch_1axc_25ns/smoke_test
```

### Unattended one-shot command

If you cannot return to the terminal during the RunPod session, use the one-shot script
instead of manually running smoke, production, analysis, and packaging commands. It does
not install or upgrade OpenMM; it uses the already-created `phase5-md` environment.

After pulling this branch on the cloud instance:

```bash
cd /workspace/GNN_PCNA
git pull
bash scripts/phase5_runpod_one_shot.sh
```

The one-shot script will:

1. activate `phase5-md`;
2. log `nvidia-smi`, OpenMM CUDA validation, smoke test, smoke analysis, production,
   production analysis, and file summaries;
3. dynamically reduce the production cost cap by the amount of budget already spent
   during checks and smoke testing;
4. package outputs and logs even if the run fails or stops on a budget guard.

Main outputs:

- log: `outputs/phase5_md/logs/one_shot_<timestamp>.log`
- package: `outputs/phase5_md/packages/phase5_time_crunch_1axc_25ns_<timestamp>_status<code>.tgz`

Optional overrides:

```bash
HOURLY_COST_USD=5.89 TOTAL_TARGET_COST_USD=27 TOTAL_HARD_COST_USD=30 \
  bash scripts/phase5_runpod_one_shot.sh
```

---

## MD Execution Plan

### Structure preparation

`scripts/phase5_prepare_1axc_openmm.py`:

1. Downloads PDB `1AXC` through PDBFixer unless a local `--input-pdb` is supplied.
2. Retains PCNA chains `A`, `C`, `E`.
3. Removes p21 peptide chains and any other non-retained chains.
4. Replaces nonstandard residues where applicable.
5. Adds missing atoms and hydrogens at pH 7.4.
6. Writes:
   - `inputs/1axc_pcna_apo_from_p21_prepared.pdb`
   - `inputs/1axc_pcna_apo_from_p21_structure_audit.json`

### Replicate generation

Three independent seeds:

- Replicate 1: `2026052901`
- Replicate 2: `2026052902`
- Replicate 3: `2026052903`

Each replicate starts from the same prepared apo-from-p21 structure but uses an
independent Langevin random seed.

### Equilibration

Per replicate:

- Energy minimization: 2000 iterations.
- NVT: 100 ps.
- NPT: 250 ps.
- Production starts only after equilibration completes.

### Production

One launch command:

```bash
python scripts/phase5_run_1axc_openmm.py \
  --output-root outputs/phase5_md/time_crunch_1axc_25ns \
  --replicates 3 \
  --production-ns 25 \
  --seeds 2026052901 2026052902 2026052903 \
  --windows 239-243 28-32 206-210 134-138 \
  --reference-window 118-122 \
  --max-wall-hours 4.0 \
  --hourly-cost-usd 6 \
  --target-cost-usd 27 \
  --hard-cost-usd 30
```

### Checkpoint/restart strategy

- Checkpoints are written every 250 ps to `replicate_XX/checkpoint.chk`.
- State logs are written every 50 ps to `replicate_XX/state.csv`.
- DCD frames are written every 100 ps to `replicate_XX/trajectory.dcd`.
- Production is chunked in 50 ps blocks so wall-time/cost guards can stop between chunks.
- Re-running the same command resumes incomplete replicates from `checkpoint.chk`.
- `COMPLETE.json` marks a replicate finished; completed replicates are skipped on rerun.

---

## Output Plan

Expected directory tree:

```text
outputs/phase5_md/time_crunch_1axc_25ns/
  MANIFEST.md
  inputs/
    1axc_pcna_apo_from_p21_prepared.pdb
    1axc_pcna_apo_from_p21_structure_audit.json
  replicate_01/
    checkpoint.chk
    state.csv
    trajectory.dcd
    progress.json
    final.pdb
    COMPLETE.json
  replicate_02/
    ...
  replicate_03/
    ...
  analysis/
    rmsd_timeseries.csv
    rmsd_timeseries.png
    window_rmsf.csv
    window_summary.csv
    window_rmsf_summary.png
    analysis_summary.json
```

Analysis command:

```bash
python scripts/phase5_analyze_1axc_md.py \
  --run-root outputs/phase5_md/time_crunch_1axc_25ns \
  --windows 239-243 28-32 206-210 134-138 \
  --reference-window 118-122
```

---

## Runtime Analysis

The project can realistically complete within the remaining ~24 hours only if the MD
run is kept to `3 x 25 ns`, analysis is first-pass only, and the pod is terminated
immediately after outputs are copied.

The original `3 x 100 ns` plan is not budget-safe. `3 x 50 ns` is scientifically better
but still unsafe under the $30 cap once setup, failed starts, and analysis overhead are
included. Single-trajectory options are cheaper but weaker for paper evidence because
governance treats a single 100 ns trajectory as exploratory and replicates are preferred.

---

## Fallback Rules

Apply these rules during the RunPod session:

1. If environment/setup takes more than 60 minutes, switch to `3 x 10 ns` or abort MD.
2. If replicate 1 at 25 ns takes more than 90 minutes, switch to `2 x 25 ns + 1 x 10 ns`.
3. If replicate 1 at 25 ns takes more than 2 hours, stop after `1 x 25 ns` and label it pilot-only.
4. If projected spend reaches `$27`, stop after the current checkpoint and analyze what exists.
5. If projected spend approaches `$30`, terminate before crossing the cap.
6. If fewer than two replicates complete, do not present replicate-supported MD evidence.
7. If equilibration is unstable, stop production and report the MD setup as not claim-eligible.

---

## Risk Assessment

### Technical risks

- B200 CUDA/OpenMM compatibility may depend on the selected container.
- PDBFixer chain handling must be audited before production.
- 1AXC apo-from-p21 may need more preparation than the short window allows.
- RunPod startup/download delays can consume the safety margin.

### Scientific risks

- 25 ns is very short for cryptic-pocket sampling.
- 1AXC is apo-from-p21, not a clean apo crystal.
- 8GLA positive-control MD is deferred.
- RMSD/RMSF alone cannot prove pocket opening or binding.

### Timeline risks

- Analysis and paper writing can be compromised if the pod is allowed to run past the
  `$27` target or 4-hour planned wall-time.
- Failed starts must not trigger repeated spending without a cutoff.

---

## Final Checklist

1. Confirm RunPod listed price before launch; do not proceed if expected cost cannot fit under `$30`.
2. Select Secure Cloud `1 x B200`, 100-200 GB disk, CUDA 12.x PyTorch/Ubuntu template.
3. Clone repo.
4. Create and activate `phase5-md`.
5. Run `python -m openmm.testInstallation`; confirm CUDA.
6. Run script `--help` checks.
7. Run the smoke test.
8. Launch the `3 x 25 ns` command.
9. Watch `state.csv`, `progress.json`, elapsed wall-time, and projected spend.
10. Apply fallback rules at the first trigger.
11. Run the analysis command.
12. Download `outputs/phase5_md/time_crunch_1axc_25ns/`.
13. Terminate the pod.
14. Use only exploratory short-timescale wording in the paper.

---

## Source and Governance References

- `reports/phase5/time_crunch_validation_plan_20260529.md`
- `reports/phase4/gate7_md_decision_draft_20260529.md`
- `reports/phase4/phase4_candidate_prioritization_20260529.md`
- `reports/phase4/gate6_authorization_20260529.md`
- `reports/phase3/model_freeze_gate4_20260529.md`
- `reports/phase3/test_evaluation_20260529.md`
- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
- `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
