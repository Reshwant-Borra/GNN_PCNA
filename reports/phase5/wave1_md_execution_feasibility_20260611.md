---
type: phase5-wave1-md-execution-feasibility
date: 2026-06-11
status: FEASIBILITY_ASSESSMENT_ONLY
md_executed: false
launch_authorized: false
---

# Wave 1 MD Execution Feasibility Assessment

## Status

This is a feasibility assessment for the completed Phase 5 official Wave 1 package.
It does not authorize MD and does not change the launch hold. No protein system setup,
minimization, equilibration, production simulation, trajectory generation, trajectory
analysis, biological interpretation, or claims were run for this assessment.

Production remains blocked fail-closed because the official package still records
`do_not_run_md: true` and no future explicit Phase 5 launch authorization exists.

## Package Scope And Simulation Count

The official Wave 1 package requires three systems, each with three 100 ns production
replicates:

| System | Replicates | Production length | Aggregate |
|---|---:|---:|---:|
| `8gla_holo_zqz` | 3 | 100 ns each | 300 ns |
| `8gla_apo_from_holo` | 3 | 100 ns each | 300 ns |
| `1axc_apo_from_p21` | 3 | 100 ns each | 300 ns |

Totals:

- Total production simulations: 9.
- Total aggregate production MD: 900 ns.
- 1AXC must not be duplicated by candidate window. One `1axc_apo_from_p21`
  trajectory set covers `239-243`, `28-32`, `206-210`, and `134-138`.
- Tier 1B windows `170-174`, `175-179`, and `152-156` remain excluded from Wave 1.

## MD Setup Accuracy Check

Verdict: preparation-level setup is accurate for the official Wave 1 package, with
documented caveats. It is not execution-ready until the launch hold is explicitly lifted.

Verified preparation facts:

- 8GLA official Wave 1 assembly is RCSB biological assembly 1, PCNA chains A/B/C.
  Deposited chain D is excluded because it belongs to assembly 2.
- 8GLA PC-118 is complete on chains A/B but incomplete on chain C because residue
  122 is missing. Positive-control metrics must account for this.
- 8GLA ZQZ ligand parameters are audited ligand-only GAFF2/AM1-BCC inputs with net
  charge 0, residue name ZQZ, and `tleap` Unit OK. They are not MD results.
- 1AXC Wave 1 uses PCNA chains A/C/E and removes p21 peptide chains B/D/F. This is
  apo-from-p21, not a clean apo crystal structure.
- 1AXC windows `239-243`, `28-32`, `206-210`, and `134-138` are complete on all
  three PCNA chains A/C/E.
- The official setup policy is consistent across systems: AMBER ff19SB, TIP3P,
  neutralization plus 150 mM NaCl, pH 7.4 standard-state protonation policy, fixed
  seeds, and identical comparable setup policy unless a deviation is documented.

Alignment caveat:

- The older 1AXC pre-registration mentions a holo/p21 comparison and a 5E0V reference.
  The official Wave 1 package authorizes only `1axc_apo_from_p21`. Future reporting
  must not rely on absent comparator trajectories unless separately authorized and run.

Governance status:

- MD may be supportive evidence only after reviewed execution and QA.
- Negative, inconclusive, and unstable outcomes remain valid.
- No wording such as "validated binding site", "drug target", "therapeutic target",
  "confirmed mechanism", or "proof of ligand binding" is allowed from this package.

## Current Local System Check

Local workstation observed on 2026-06-11:

| Component | Observed value |
|---|---|
| System | Alienware Aurora R16 |
| CPU | Intel Core i7-14700F, 20 cores, 28 logical processors |
| RAM | 34,064,277,504 bytes physical memory, about 31.7 GiB |
| GPU | NVIDIA GeForce RTX 4070 |
| GPU memory | 12,282 MiB by `nvidia-smi` |
| Driver / CUDA | NVIDIA driver 581.95, CUDA 13.0 by `nvidia-smi` |
| C: free space | 56,292,143,104 bytes, about 52.4 GiB |

Local feasibility:

- The local RTX 4070 may be useful for short setup validation or a small benchmark,
  but it is not the recommended execution platform for full Wave 1.
- The 12 GB GPU memory may be tight for explicit-solvent PCNA trimers depending on
  box size and engine settings.
- The current C: free space is insufficient for a safe full Wave 1 output archive.
  A full run should use external scratch or cloud/local storage with at least 500 GB
  free, preferably 1 TB.

## Wall-Clock Runtime Estimates

These are production-only planning estimates. They exclude system preparation,
minimization, equilibration, transfer time, queue time, failed retries, and post-run
analysis. Exact throughput requires a short benchmark after prepared solvated systems
exist.

Assumed throughput bands for explicit-solvent PCNA trimer workloads:

| GPU | Assumed throughput | One 100 ns replicate | 900 ns sequential on one GPU | Ideal 9-GPU makespan |
|---|---:|---:|---:|---:|
| RTX 4070 | 120-220 ns/day | 10.9-20.0 h | 98-180 h, 4.1-7.5 d | 10.9-20.0 h |
| L4 | 70-130 ns/day | 18.5-34.3 h | 166-309 h, 6.9-12.9 d | 18.5-34.3 h |
| L40S | 250-450 ns/day | 5.3-9.6 h | 48-86 h, 2.0-3.6 d | 5.3-9.6 h |
| H200 | 450-750 ns/day | 3.2-5.3 h | 29-48 h, 1.2-2.0 d | 3.2-5.3 h |
| B200 | 600-1000 ns/day | 2.4-4.0 h | 22-36 h, 0.9-1.5 d | 2.4-4.0 h |

AMBER-style production should be parallelized by independent replicate. Do not assume
that one 100 ns trajectory will scale efficiently across multiple GPUs.

## Cloud Cost Estimates

Cost formula: production GPU-hours multiplied by GPU or instance hourly price. The
production GPU-hour range equals the sequential one-GPU production wall-clock range
above. Parallel execution reduces calendar time but not total GPU-hours.

The estimates below are planning estimates from public pricing sources checked on
2026-06-11. They exclude storage, egress, taxes, failed retries, setup overhead, and
idle time. Add a 20-40% operational buffer for a real launch budget.

### Lowest Public / Marketplace Pricing Basis

This basis uses low public marketplace or neocloud rates when available.

| GPU | Planning price used | Estimated production cost |
|---|---:|---:|
| RTX 4070 / similar consumer class | $0.12/hr | $12-$22 |
| L4 | $0.13/hr | $22-$40 |
| L40S | $0.80/hr | $38-$69 |
| H200 | $3.14/hr | $90-$151 |
| B200 | $5.87/hr | $127-$211 |

### RunPod / Lambda-Style Pricing Basis

This basis uses public GPU rental pricing from RunPod/Lambda-style providers where
available. RTX 4070 and L4 availability is marketplace-dependent.

| GPU | Planning price used | Estimated production cost |
|---|---:|---:|
| RTX 4070 / similar consumer class | $0.12/hr | $12-$22 |
| L4 | $0.39/hr | $65-$120 |
| L40S | $0.86/hr | $41-$74 |
| H200 | $4.39/hr | $126-$211 |
| B200 | $6.89/hr | $149-$248 |

### Major Cloud Pricing Basis

This basis uses AWS-style public pricing where the GPU is available. RTX 4070 is not a
standard major-cloud GPU instance class.

| GPU | Planning price used | Estimated production cost |
|---|---:|---:|
| RTX 4070 | Not generally available | N/A |
| L4 | $0.8048/hr | $134-$248 |
| L40S | $1.861/hr | $89-$161 |
| H200 | $4.975/hr | $143-$239 |
| B200 | $14.2416/hr | $308-$513 |

Pricing notes:

- AWS G6 provides L4 instances; Vantage lists `g6.xlarge` from $0.8048/hr.
- AWS G6e provides L40S instances; Vantage lists `g6e.xlarge` from $1.861/hr.
- AWS P5e capacity-block pricing lists H200 at about $4.975 per accelerator-hour in
  multiple regions.
- AWS P6-B200 uses 8 B200 GPUs; Vantage lists `p6-b200.48xlarge` at $113.9328/hr,
  about $14.2416 per GPU-hour.
- RunPod lists H200 at $4.39/hr and B200 at $5.89/hr in the pricing page snapshot.
- Lambda lists B200 per-GPU on-demand prices around $6.69-$6.99/hr depending on size.
- Public aggregators list L4 marketplace ranges near $0.13/hr at the low end; rates
  can change quickly.

## Recommended Execution Platform

Recommended platform: L40S.

Reasoning:

- L40S provides 48 GB VRAM, materially safer than the local RTX 4070 or cloud L4 for
  explicit-solvent PCNA trimer systems.
- L40S is fast enough for one 100 ns replicate in roughly 5-10 hours under the planning
  throughput assumption.
- It is much cheaper than H200/B200 for this workload while still giving practical
  calendar time.
- H200 and B200 are technically feasible but cost-inefficient unless a strict deadline
  or availability constraint dominates.

Recommended execution shapes after explicit future launch authorization:

- Budget-conscious: 3 x L40S, one system wave at a time, roughly 16-29 production
  hours plus overhead.
- Fast: 9 x L40S, one GPU per replicate, roughly 5-10 production hours plus overhead.
- Fallback: 3-9 x L4 if slower wall-clock is acceptable and memory is sufficient after
  a short benchmark.

The current local RTX 4070 workstation is not recommended for full Wave 1 because of
VRAM uncertainty and insufficient local free storage.

## Parallelization Opportunities

- Run the nine production replicates independently.
- Use one GPU per replicate.
- Run trajectory QA as each replicate completes.
- Keep analysis separate from production nodes.
- Avoid duplicating 1AXC production trajectories by residue window.
- Avoid trying to accelerate a single replicate with multiple GPUs unless a benchmark
  proves efficiency for the exact engine and prepared system.

## Storage And Output Size

Expected size depends on atom count, trajectory format, and frame interval. Prepared
solvated systems do not yet exist, so these are planning estimates.

| Output policy | Expected trajectory size | Expected Wave 1 total |
|---|---:|---:|
| Lean archive, 100 ps frames | about 1-4 GB per trajectory | about 25-75 GB with logs and analysis |
| Analysis-rich, 10 ps frames | about 10-40 GB per trajectory | about 200-500 GB |
| Very dense frames | not recommended | can exceed 1 TB |

Recommended storage:

- Minimum scratch: 500 GB free.
- Comfortable scratch: 1 TB local NVMe or cloud block/local SSD.
- Keep large trajectories outside git.
- Commit only manifests, hashes, selected reports, QA summaries, and reviewed
  interpretation artifacts.

## Recommended Launch Strategy

This is a strategy for a later authorized launch only; it is not launch authorization.

1. Preserve the current fail-closed state until an explicit future launch authorization
   exists and the official `do_not_run_md` hold is intentionally superseded.
2. Prepare systems with complete manifests, input hashes, environment capture, and
   setup command logs.
3. Run a short benchmark/preflight segment per system after preparation, before full
   production, to measure atom count, memory use, ns/day, stability, and output size.
4. If benchmark and equilibration QA pass, launch one GPU per replicate, ideally on
   L40S.
5. Write per-replicate completion records, output hashes, seeds, command lines, and
   environment records.
6. Run trajectory QA before any scientific interpretation.
7. Treat negative, unstable, or inconclusive outcomes as valid evidence under the
   pre-registration rules.
8. Require human review of first MD interpretation and claim audit before any report
   or figure uses MD results.

## External Pricing And Performance Sources Checked

- RunPod GPU pricing: https://www.runpod.io/pricing
- Lambda pricing and instances: https://lambda.ai/pricing and https://lambda.ai/instances
- AWS G6 L4 instance family: https://aws.amazon.com/ec2/instance-types/g6/
- AWS G6e L40S instance family: https://aws.amazon.com/ec2/instance-types/g6e/
- AWS P5/P5e H100/H200 instance family: https://aws.amazon.com/ec2/instance-types/p5/
- AWS P6-B200 instance family: https://aws.amazon.com/ec2/instance-types/p6/
- AWS EC2 Capacity Blocks pricing: https://aws.amazon.com/ec2/capacityblocks/pricing/
- Vantage AWS instance pricing for `g6.xlarge`, `g6e.xlarge`, and `p6-b200.48xlarge`:
  https://instances.vantage.sh/aws/ec2/g6.xlarge,
  https://instances.vantage.sh/aws/ec2/g6e.xlarge,
  https://instances.vantage.sh/aws/ec2/p6-b200.48xlarge
- GPU marketplace pricing indices:
  https://getdeploying.com/gpus,
  https://getdeploying.com/gpus/nvidia-l4,
  https://gpuperhour.com/providers/runpod
- Additional neocloud pricing context:
  https://northflank.com/blog/runpod-gpu-pricing,
  https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/,
  https://www.spheron.network/blog/gpu-cloud-benchmarks/
- AMBER/NVIDIA MD benchmark context:
  https://www.exxactcorp.com/blog/molecular-dynamics/amber-molecular-dynamics-nvidia-gpu-benchmarks,
  https://developer.nvidia.com/hpc-application-performance

## Evidence Status

Evidence status: verified for local Wave 1 package facts and local hardware inspection;
inferred for runtime, cost, and storage estimates; no MD outcome evidence exists.

Confidence: high for simulation count, package scope, fail-closed launch status, chain
and window facts, and ZQZ parameter audit status. Medium for runtime and storage
estimates until prepared systems and a short benchmark exist. Medium for cloud cost
because GPU prices and availability change quickly.

Primary local sources:

- `reports/phase5/official_wave1_execution_package_20260609.md`
- `reports/phase5/wave1_readiness_report_20260610.md`
- `reports/phase5/8gla_preparation_audit_20260610.md`
- `reports/phase5/1axc_preparation_audit_20260610.md`
- `reports/phase5/zqz_parameter_audit_20260611.md`
- `data/registries/phase5_wave1_preparation_audit_20260610.json`
- `reports/phase4/md/8gla/pre_registration.md`
- `reports/phase4/md/1axc/pre_registration.md`

Governance:

- `docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md`
- `docs/scientific_governance/13_MD_VALIDATION_RULES.md`
- `docs/scientific_governance/14_CLAIM_POLICY.md`
- `docs/scientific_governance/15_PROVENANCE_AND_REPRODUCIBILITY.md`
- `docs/scientific_governance/19_STOP_CONDITIONS.md`
- `docs/scientific_governance/26_HUMAN_REVIEW_GATES.md`
- `docs/scientific_governance/33_PRE_MD_REALITY_CHECK.md`
