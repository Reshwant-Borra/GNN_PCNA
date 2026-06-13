---
type: phase5-wave1-gpu-time-estimates
date: 2026-06-12
status: PLANNING_ESTIMATES_ONLY_MD_BLOCKED
md_executed: false
launch_authorized: false
do_not_run_md: true
source_reports:
  - reports/phase5/wave1_md_execution_feasibility_20260611.md
  - reports/phase5/wave1_readiness_report_20260610.md
  - reports/phase5/human_review_decision_package_20260612.md
---

# Phase 5 Wave 1 GPU Time Estimates

## Scope

This addendum documents planning-only runtime estimates for the approved Phase 5
Wave 1 policy after human review resolved the ZQZ and force-field/water decisions.
It does not authorize launch and does not execute MD setup, minimization,
equilibration, production, trajectory generation, trajectory analysis,
interpretation, or claims.

Approved setup policy for future launch consideration:

- Protein force field: AMBER ff19SB.
- Water model: OPC.
- Ion parameters: Joung-Cheatham OPC-compatible ions.
- ZQZ ligand package: deprotonated ZQZ, net charge -1, GAFF2/AM1-BCC.

Wave 1 production scope remains:

- 3 systems.
- 3 replicates per system.
- 100 ns per replicate.
- 9 independent production simulations.
- 900 ns aggregate production MD.

## Runtime Estimate Table

These estimates are production-only wall-clock estimates. They exclude structure
preparation, solvation, ion placement, minimization, equilibration, checkpoint
handling, transfer time, failed-job recovery, and post-run analysis. They assume one
GPU per independent replicate. They do not assume efficient multi-GPU scaling for a
single trajectory.

| GPU class | Planning throughput | One 100 ns replicate | 900 ns sequential on 1 GPU | 3 GPUs, one system wave at a time | 9 GPUs, all replicates parallel |
|---|---:|---:|---:|---:|---:|
| RTX 4070 12 GB | 120-220 ns/day | 10.9-20.0 h | 4.1-7.5 d | 1.4-2.5 d | 10.9-20.0 h |
| NVIDIA L4 24 GB | 70-130 ns/day | 18.5-34.3 h | 6.9-12.9 d | 2.3-4.3 d | 18.5-34.3 h |
| NVIDIA L40S 48 GB | 250-450 ns/day | 5.3-9.6 h | 2.0-3.6 d | 16.0-28.8 h | 5.3-9.6 h |
| NVIDIA A100 40/80 GB | 300-550 ns/day | 4.4-8.0 h | 1.6-3.0 d | 13.1-24.0 h | 4.4-8.0 h |
| NVIDIA H100 80 GB | 400-700 ns/day | 3.4-6.0 h | 1.3-2.3 d | 10.3-18.0 h | 3.4-6.0 h |
| NVIDIA H200 141 GB | 450-750 ns/day | 3.2-5.3 h | 1.2-2.0 d | 9.6-16.0 h | 3.2-5.3 h |
| NVIDIA B200 class | 600-1000 ns/day | 2.4-4.0 h | 0.9-1.5 d | 7.2-12.0 h | 2.4-4.0 h |

## Recommended Execution Shape After Future Authorization

Recommended platform remains L40S unless a benchmark shows a better cost/runtime
choice for the prepared PCNA systems.

Practical launch shapes after future explicit authorization:

- Budget-conscious: 3 x L40S, one system wave at a time, about 16-29 production
  hours plus setup, equilibration, transfer, and QA overhead.
- Fast: 9 x L40S, one GPU per replicate, about 5-10 production hours plus overhead.
- Local RTX 4070: not recommended for full Wave 1 because 12 GB VRAM may be tight for
  explicit-solvent PCNA trimers and the workstation storage headroom is limited.

## Required Benchmark Before Treating Estimates As Operational

Before launch budgeting or scheduling can rely on these estimates, a future
authorized setup/benchmark step must record:

- prepared atom counts for all three systems;
- GPU memory use;
- measured ns/day for a short benchmark;
- output size at the chosen frame interval;
- software versions, command lines, seeds, hashes, and hardware details;
- whether ff19SB + OPC + Joung-Cheatham OPC-compatible ions runs stably under the
  chosen MD engine.

## Evidence Status

Evidence status: inferred planning estimate from the existing Phase 5 feasibility
report and the approved human-review policy. No prepared solvated systems or
benchmarks exist in this package, and no MD outcome evidence exists.

Confidence: high for Wave 1 run count and aggregate nanoseconds; medium-low for
runtime estimates until prepared-system benchmarks are available.
