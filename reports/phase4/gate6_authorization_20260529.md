---
type: phase4-gate6-authorization
date: 2026-05-29
decision: APPROVED
decision_id: phase4_pcna_inference_gate6_20260529
authorized_by: Reshwant-Borra
governance:
  - docs/scientific_governance/12_PCNA_SPECIFIC_CHECKS.md
  - docs/scientific_governance/14_CLAIM_POLICY.md
  - docs/scientific_governance/09_EVALUATION_PROTOCOL.md
frozen_checkpoint: checkpoints/phase3/spatial_only_fold1_seed1_best.pt
gate5_record: reports/phase3/test_evaluation_20260529.md
---

# GATE 6 Authorization — Phase 4 PCNA Inference

## Decision

**APPROVED** — Phase 4 PCNA inference may proceed under the scope and constraints below.

## Primary Inference Dataset

`C:\Users\reshw\phase4_pcna_crawl` — 103 mmCIF structures (SHA256 verified, 0 errors).

| Part | Count | Description |
|---|---|---|
| 1 | 56 | Ranked PCNA candidates (47 ligand-bound, 7 apo/no-ligand, +2 extras) |
| 2A | 17 | Additional human PCNA P12004, not in ranked list |
| 2C | 30 | Archaeal/yeast/other sliding clamp homologs |

## Authorized Scope

1. Run inference on all 103 structures using the frozen checkpoint `spatial_only_fold1_seed1_best.pt`.
2. **8GLA** is a positive-control sanity check only. Recovery of the AOH1996/ZQZ contact region does NOT validate novel-site predictions (governance doc 12).
3. Prioritize interpretation of human PCNA (Part 1, Part 2A) structures.
4. **5E0V** included in inference but classified as `VARIANT_NOT_APO` (S228I mutation + FEN1 peptide). Results must not be interpreted as wild-type PCNA behavior.
5. Part 2C (homologs): secondary comparative analysis only; not part of the primary claim path.
6. Generate all required governance artifacts before interpretation: ranked candidates, PCNA-specific audit, interface-overlap analysis, candidate prioritization report.
7. **No MD yet.**
8. **No therapeutic, clinical, validated-site, or druggability claims.**

## Authorized Claim Language (per doc 14)

- "candidate PCNA cryptic pocket region"
- "computationally predicted PCNA surface region"
- "overlaps a known PCNA interaction interface"
- "positive-control recovery of the AOH1996/8GLA region"
- "hypothesis-generating site for follow-up"

## Forbidden Claim Language

- "validated PCNA drug target"
- "new therapeutic site"
- "confirmed resistance-proof pocket"
- "druggable site"
- "AOH1996 mechanism proven by the model"
- Any clinical or treatment claim

## Model and Architecture

| Property | Value |
|---|---|
| Checkpoint | `checkpoints/phase3/spatial_only_fold1_seed1_best.pt` |
| Architecture | GraphSAGE-3L, spatial edges only (edge_type==0, 8Å CA cutoff) |
| Input features | 25-dim (22 one-hot AA + 3 binary flags) — no ESM |
| Val macro-AUPRC at freeze | 0.2047 (fold=1, seed=1) |
| Test macro-AUPRC | 0.2034 [0.1825, 0.2275] |

## Required Outputs

1. `reports/phase4/phase4_inference_results_20260529.json` — per-residue scores (machine-readable)
2. `reports/phase4/phase4_candidate_report_20260529.md` — ranked candidate regions
3. `reports/phase4/phase4_pcna_audit_20260529.md` — PCNA-specific governance audit
4. `reports/phase4/phase4_interface_overlap_20260529.md` — interface-overlap analysis
5. `reports/phase4/phase4_candidate_prioritization_20260529.md` — Phase 5 MD candidate list

## Provenance

- GATE 5 cleared: `reports/phase3/test_evaluation_20260529.md`
- Crawl manifest: `C:\Users\reshw\phase4_pcna_crawl\phase4_crawl_manifest.json`
- Interface map: `data/registries/pcna_interface_map.json`
- Candidate manifest: `data/registries/phase4_candidate_manifest.json`
