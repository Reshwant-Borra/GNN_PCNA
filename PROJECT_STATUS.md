# Project Status

Last synchronized: 2026-08-16

## Reconciliation Verdict

Repository reconciliation is currently **NO-GO** for full historical reproducibility.

Forward MD execution is now launcher-gated through `md.sh`, and the analysis/control gate has been repaired to reject static starting-state differences alone. However, the historical 520-dim GNN lineage is not yet fully reproducible from one committed clone because the exact 520-dim label manifest, graph manifest file, explicit model config, durable checkpoint retrieval, and frozen-output identity reproduction remain unresolved.

## Current Objective

The GNN identifies where on PCNA to investigate. MD tests whether that frozen predicted region reproducibly exhibits predefined accessibility, geometry, flexibility, correlated-motion, or cavity-like dynamics under the simulated conditions.

MD does not directly prove ligand binding, druggability, therapeutic relevance, or experimental existence of a cryptic pocket.

## Frozen GNN Hypothesis

Source artifacts:

- `md_validation_4070/pockets/final_consensus_1w60_20260815.json`
- `md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json`
- `artifacts/final_benchmark_expansion_20260815/md_handoff_packet.json`

Frozen extraction policy: `independent_mcc_rank_fraction_size_weighted_cluster`.

Mean literal Jaccard: `0.6792` (`0.6791537667698658` in the frozen protocol).

Interpretation: `MODERATE / EXPLORATORY PASS`.

CORE 3/3:

- A:25, A:26, A:38, A:39, A:40, A:41, A:42, A:44, A:45, A:46, A:47

SUPPORTED 2/3:

- A:27, A:43, A:232, A:233, A:234

UNCERTAIN 1/3:

- A:231, A:250, A:251, A:252

The primary MD region is the >=2/3 supported region, with the 3/3 core reported separately. The 1/3 residues are exploratory fringe only and must not silently redefine the candidate.

## Current Structures

- `1W60`: apo/candidate structure.
- `8GLA`: open/reference control structure; ligand stripped for protein-only MD.
- PCNA is modeled as a 3-chain homotrimer.
- Biological assemblies are generated with `gemmi`; protein chains with at least 200 residues are retained, ligands/waters/short peptides are stripped, chains are renamed A/B/C, and PDBFixer repairs atoms and protonates at pH 7.4.
- Candidate residues use PDB author/auth_seq_id numbering from 1W60 chain A; analysis currently maps the target region to prepared chain index 0.

Current structure caveats:

- `1W60`: 3.15 A resolution, 3-chain assembly generated from assembly 1, no internal residues rebuilt in preflight, no declared disulfides.
- `8GLA`: 3.77 A resolution, 3-chain assembly generated from assembly 1, 50 internal residues rebuilt in preflight, declared Cys135-Cys162 disulfides, and severe generated-coordinate close contacts before minimization.
- Preparation is smoke-ready/preflight-passed, not production-approved.

## Current MD Protocol

Source of truth: `md_validation_4070/run_md.py` plus launcher defaults in `md.sh`.

- Force field: `amber14-all.xml`
- Water model: `amber14/tip3p.xml` / TIP3P
- Ionic strength: neutralized, 0.15 M NaCl
- Temperature: 310 K
- Pressure: 1 bar
- Electrostatics: PME
- Nonbonded cutoff: 1.0 nm
- Constraints: HBonds, rigid water
- HMR: enabled by default, 4.0 amu hydrogen mass
- Timestep: 4 fs with HMR, 2 fs if HMR disabled
- Padding: 1.0 nm
- Integrator: OpenMM `LangevinMiddleIntegrator`, 1/ps friction
- Thermostat: Langevin middle integrator at 310 K
- Barostat: `MonteCarloBarostat`, 1 bar, 310 K, frequency 25, seeded
- Minimization: 5000 iterations default
- Equilibration: 2.0 ns default
- Trajectory/log output interval: 50 ps
- Checkpoint interval: 10 ps
- Seeds: deterministic per replicate, `20260001`, `20260002`, `20260003`
- Production plan: 3 x 100 ns `8GLA` control and 3 x 100 ns `1W60` apo/candidate
- Aggregate production duration: 600 ns
- CUDA: required by `md.sh` MD stages through `--require-platform`
- CUDA precision: `mixed`

## Current Analysis Protocol

Source of truth: `md_validation_4070/analyze_md.py` and `md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json`.

Frozen protocol SHA-256 after reconciliation:

```text
587f27cf2e402fe50b264d98d3d60fbbdcc8f9095025b2a89d12c7aebd633e56
```

Previous claimed protocol SHA-256 before the static-control repair:

```text
2497def9e4675538dd08051ae6e5a448a41fbd32a1d7dc59cfb528d74d64ce3c
```

Implemented metrics:

- RMSD: global/stability and PBC-artifact sanity check after imaging and alignment.
- RMSF: local flexibility measure; high RMSF alone is not pocket evidence.
- SASA: local accessibility measure with atom-key parity across apo/control.
- DCCM: correlated-motion summary, qualitative/supportive unless replicate-stable.
- Region geometry/openness: supported-region SASA and CA convex-hull thresholds.
- Convex hull: CA convex-hull volume descriptor, not a ligand-volume estimate.
- Core/support/fringe analysis: `core_3of3`, `supported_ge2of3`, `supported_fringe_2of3`, `seed_specific_uncertain_fringe_1of3`, and `full_union_exploratory` when available.
- Positive-control interpretability: trajectory-derived control gate requiring complete 3 x 5 ns control replicates, artifact-free trajectories, open-like behavior under frozen thresholds, and non-trivial local RMSF. Static 8GLA-vs-1W60 starting-state separation is descriptive only and cannot pass the gate.

No implemented MDpocket/fpocket cavity-volume metric is part of the frozen analysis. Do not document such a metric as current unless code is added and the frozen protocol is intentionally revised before candidate production.

## Validation State

- GNN handoff integrity: **not historically proven**; see `artifacts/provenance/FROZEN_GNN_PROVENANCE.json`.
- Structure/preparation validation: preflight PASS for smoke-readiness; not production approval.
- MD parameter validation: current defaults audited.
- Frozen analysis protocol: reconciled and hashed.
- Static analysis validation: partial static pass; trajectory validation pending.
- Infrastructure interruption/resume: validated as infrastructure only on disposable runs, not scientific MD evidence.
- RTX 4070 smoke test: not yet passed in current status artifacts.
- Control-first validation: not executed/passed in current status artifacts.
- Historical 520-dim GNN provenance: unresolved because label manifest, graph manifest file, explicit config, durable checkpoint retrieval, and frozen-output identity reproduction are missing.

## Production Gate State

PRODUCTION BLOCKED: Gate-6 human approval required.

Current `research_os_memory/HUMAN_DECISIONS.md` does not record Gate-6 approval. The production launcher also blocks macOS production and requires CUDA on the execution host.

## Hardware Plan

- Mac: code review, documentation, static checks, and lightweight preparation/audits when practical. Not intended for production MD.
- RTX 4070: smoke testing, 3 x 5 ns control-first validation, and local benchmarking/validation.
- Cloud NVIDIA GPU: production MD and, when operationally supported, independent single-GPU replicate jobs.

Scientific parameters must not silently change between GPUs. Record GPU, driver, CUDA, OpenMM, precision, git state, and hashes in provenance.

## Exact Next Step

Run the 0.1 ns RTX 4070 smoke test through the launcher:

```bash
./md.sh smoke
```

Do not treat a successful smoke run as historical GNN provenance. The remaining GNN provenance blockers in `REPRODUCIBILITY_MANIFEST.json` must be resolved before claiming one-commit historical reproducibility.

## Authoritative Documentation

- Primary current status: `PROJECT_STATUS.md`
- Practical execution runbook: `md_validation_4070/FINAL_MD_EXECUTION_INSTRUCTIONS.md`
- Launcher details and restart files: `md_validation_4070/MD_EXECUTION_RUNBOOK.md`
- Frozen analysis: `md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json`
- Structure validation: `md_validation_4070/MD_STRUCTURE_VALIDATION_REPORT.md`
- Parameter audit: `md_validation_4070/MD_PARAMETER_AUDIT.md`
- Chain/residue mapping: `md_validation_4070/PCNA_CHAIN_AND_RESIDUE_MAPPING.md`
