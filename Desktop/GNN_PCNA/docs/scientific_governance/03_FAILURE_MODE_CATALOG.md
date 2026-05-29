# Failure Mode Catalog

## Purpose

Catalog the ways Phase 2 can produce scientifically invalid work even when code runs and metrics look good.

## Hard Rules

- Every major pipeline stage must be audited against this catalog.
- A detected stop condition invokes [19_STOP_CONDITIONS.md](19_STOP_CONDITIONS.md).
- Failure modes are scientific blockers, not cosmetic warnings.

## Catalog

| Failure mode | Description | Example in GNN-PCNA | Why dangerous | Prevention rule | Detection method | Stop condition | Remediation |
|---|---|---|---|---|---|---|---|
| Code works but implements wrong science | Software succeeds while method violates protocol. | Graphs generated before split or with stale labels. | Invalid metrics can look polished. | Map code to governance docs. | Code-rule trace audit. | Rule mismatch. | Rewrite and rerun from raw inputs. |
| Agent invents assumptions | Agent fills biology gaps. | Claims AOH1996 proves a new allosteric mechanism. | Hallucinated science contaminates design. | Use [02_ASSUMPTION_REGISTRY.md](02_ASSUMPTION_REGISTRY.md). | Prompt and diff review. | Undocumented assumption found. | Document, review, rerun. |
| Dataset labels are wrong | Positives/negatives do not match definition. | C-alpha labels described as curated cryptic labels. | Model learns proxy while report claims biology. | Freeze label definition. | Label audit and spot checks. | Label uncertainty affects claims. | Relabel or narrow claims. |
| Split leakage | Same or related systems appear across splits. | Apo/holo pair split between train and test. | Test no longer estimates generalization. | Split before graph generation. | Split audit. | Leakage found. | New split, new graphs, retrain. |
| Homolog leakage | Sequence-related proteins cross splits. | Same family or high-identity homolog in train/test. | Inflated metrics. | Sequence clustering required. | MMseqs/CD-HIT audit. | Homologs cross split. | Regroup cluster. |
| Apo/holo leakage | Conformations of same protein cross splits. | Apo PCNA train, holo PCNA test. | Model memorizes protein. | Group apo/holo by system. | PDB/UniProt grouping. | Same system cross split. | Move group to one split. |
| Model learns shortcuts | Nonbiological feature predicts labels. | Chain ID or residue number correlates with positives. | Looks accurate but fails transfer. | Shortcut-feature audit. | Ablations and permutation tests. | Shortcut drives metrics. | Remove feature or prove necessity. |
| Chain ID shortcut | Chain encoding leaks ligand location. | 8GLA ligand only on chains A/B; model learns chain. | PCNA predictions biased by chain labels. | Justify and ablate chain features. | No-chain-ID ablation. | Large drop or artifact. | Remove or restrict. |
| Residue index shortcut | Residue number leaks pocket. | AOH region around L126/Y133 hardcoded by index. | Not transferable. | No raw index unless justified. | Residue-index permutation. | Index predicts labels. | Remove feature. |
| Graph size shortcut | Protein size correlates with label prevalence. | Large graphs get lower scores regardless of pockets. | Per-protein ranking invalid. | Per-protein metrics. | Size-performance correlation. | Strong size shortcut. | Normalize and audit. |
| Batch leakage | Batched graphs mixed in aggregation. | `h.mean(dim=0)` across PyG batch. | Proteins influence each other. | Use batch-aware scatter. | Batch-isolation test. | Cross-graph influence. | Patch architecture. |
| Preprocessing changes biology | Parser silently drops chains/residues. | PCNA trimer reduced to asymmetric unit without notice. | Wrong biological context. | Raw structure validation. | Chain/residue audit. | Missing required chain. | Rebuild with policy. |
| Wrong chain mapping | PCNA chains misidentified. | Polymerase chain annotated as PCNA. | False pocket/interface claims. | Chain whitelist and mapping table. | Structure mapping audit. | Chain identity unclear. | Manual review. |
| Missing residues mishandled | Gaps treated as real adjacency. | Missing loop bridged by sequence edge. | Fake graph geometry. | Gap-aware edges. | Residue numbering audit. | Unresolved gap at target site. | Mask or exclude. |
| Alternate conformations mishandled | AltLoc atoms mixed incorrectly. | Pocket side chain chosen inconsistently. | Label noise and graph mismatch. | Document AltLoc rule. | PDB parser audit. | AltLoc affects label. | Reparse deterministically. |
| Old artifacts contaminate Phase 2 | V1 graphs/checkpoints reused. | `best.ckpt` loaded without manifest. | Invalid provenance. | Source-of-truth manifest. | Hash audit. | Unregistered artifact. | Quarantine and regenerate. |
| Metrics look good but mean little | AUROC high under imbalance. | High AUROC, weak AUPRC/top-k. | Overconfidence. | AUPRC, top-k, calibration, CIs. | Metrics audit. | Primary metrics fail. | Report honestly or revise. |
| Validation set becomes test set | Repeated val decisions reported as final. | Combined val/test headline. | Inflated evidence. | Test once after freeze. | Evaluation log audit. | Test touched early. | New untouched test. |
| Baselines too weak | GNN compared only to random. | No fpocket/P2Rank/PocketMiner where applicable. | Superiority claim unsupported. | Required baselines. | Baseline audit. | Baselines missing. | Run baselines or remove claim. |
| MD result unexpected | Simulation disagrees with hypothesis. | Pocket does not open. | Team may force story. | Unexpected results policy. | MD interpretation audit. | Interpretation forced. | Reframe as evidence. |
| MD result overinterpreted | Dynamics treated as proof. | RMSF change claimed as binding validation. | Therapeutic overclaim. | MD is supportive only. | Claim audit. | Claim exceeds MD. | Downgrade claim. |
| Biological realism missing | Prediction not structurally plausible. | Buried inaccessible residue cluster called pocket. | Science invalid despite metrics. | Biological realism audit. | SASA/interface/conservation checks. | Implausible site. | Reject or reclassify. |
| Predictions conflict with PCNA trimer biology | Site breaks ring logic or maps to impossible chain. | Site inside trimer interface without stability analysis. | PCNA biology ignored. | PCNA-specific checks. | Trimer mapping audit. | Conflict unresolved. | Human review. |
| Paper overclaims | Wording outruns evidence. | "validated drug target." | Misleads readers. | Claim policy. | Claim audit. | Forbidden wording. | Rewrite. |
| Coding agent confidently patches wrong logic | Agent edits methodology without approval. | Changes label threshold to improve AUPRC. | Silent scientific drift. | Agent rules. | Diff and prompt audit. | Unauthorized method change. | Revert or review. |
| ResearchOS produces fake confidence | Multi-source summary lacks verification. | High confidence from many weak sources. | Bad context drives code. | Critic-planner flow. | Evidence audit. | Unsupported confidence. | Replan. |
| Source corpus large but not actionable | Thousands of sources, no requirements. | Crawl folder used as authority. | Noise masquerades as rigor. | Source index triage. | Requirement traceability. | No decisive source. | Narrow question. |
| Project becomes infrastructure instead of science | Tools grow while core validation absent. | UI before split audit. | Delays science gates. | Build checklist order. | Milestone audit. | Gate bypass. | Return to gate. |
| Scope explodes | Adds docking, networks, omics without gate. | New cancer claims from expression data. | Dilutes validation. | Claim and assumption registry. | Scope review. | Unapproved scope. | Park item. |
| Source of truth unclear | Multiple paths claim truth. | Obsidian copy conflicts with repo. | Artifact drift. | Source-of-truth audit. | Hash/path audit. | Canonical path missing. | Freeze and reconcile. |
| Results do not match expectations and team tries to force them | Evidence is reshaped to original story. | Baseline beats GNN but report claims novelty. | Scientific misconduct risk. | Unexpected results policy. | Contradiction audit. | Forced interpretation. | Rewrite scientific question. |

## Required Checks

At each readiness gate, mark each relevant failure mode as `not applicable`, `checked-pass`, `warning`, or `fail`.

## Forbidden Actions

- Marking a failure mode "not applicable" because it is inconvenient.
- Continuing downstream work after a stop condition is triggered.
- Hiding a failure mode in narrative text instead of logging it.

## Examples Of Failure

- A high AUROC run is promoted even after split leakage is detected.
- A no-chain-ID ablation is skipped because the current model performs well.
- Unexpected MD is reframed as "bad simulation" without pre-registered criteria.

## Prevention

Run this catalog at every readiness gate and attach the checked table to the audit packet.

## Compliance Artifact

`reports/phase2/failure_mode_audit.md`.

## If This File Is Ignored

Any downstream result is governance-noncompliant and cannot support Phase 2 claims.
