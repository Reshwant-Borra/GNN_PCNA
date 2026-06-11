---
type: phase5-manifest-provenance-template-report
date: 2026-06-10
status: TEMPLATE_ONLY
md_executed: false
---

# Manifest And Provenance Templates - Phase 5 Wave 1

## Required Hashes

- Source mmCIF and metadata SHA256.
- Prepared coordinate and topology hashes.
- ZQZ parameter file hashes.
- Per-replicate input hashes before minimization, equilibration, and production.
- Per-replicate output hashes after each future stage.
- Manifest hash for every upstream manifest consumed.

## Environment Capture

Each future launch manifest must capture git commit, branch, dirty state, hostname,
OS/platform, Python version, AmberTools/Amber versions, CUDA/GPU details if applicable,
loaded modules or conda environment, `AMBERHOME`, and relevant environment variables.

## Seed Recording

Use the official seeds:

| System | Replicate 1 | Replicate 2 | Replicate 3 |
|---|---:|---:|---:|
| `8gla_holo_zqz` | 2026060911 | 2026060912 | 2026060913 |
| `8gla_apo_from_holo` | 2026060921 | 2026060922 | 2026060923 |
| `1axc_apo_from_p21` | 2026060931 | 2026060932 | 2026060933 |

Any seed change must be documented as a planned deviation before execution.

## Command Logging

Every future setup and execution command must be written to the manifest before it is
run and copied to a command log afterward with exit code, start/end timestamps, working
directory, stdout/stderr log paths, and output hashes.

## Stop-Condition Recording

The templates include a stop-condition table for unresolved assembly mapping, missing
candidate residues, missing or unaudited ZQZ parameters, launch authorization absence,
unstable equilibration, trimer-integrity loss, environment capture failure, unexpected
trajectory files, and claim/interpretation attempts before human review.

Template files were written under:

`outputs/phase5_md/official_wave1_20260609/`

Evidence status: template/provenance infrastructure only. No MD stage was run.
