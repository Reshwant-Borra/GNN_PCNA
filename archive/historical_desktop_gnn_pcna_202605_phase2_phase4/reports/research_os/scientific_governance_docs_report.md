# Scientific Governance Docs Report

## Purpose

This report records the Phase 2 scientific governance documentation created for GNN-PCNA. The docs are designed to prevent Version 1-style failure modes before any model training, scientific model edits, MD interpretation, or claims.

## Context Reviewed

- Local SARC proposal: `BORRA_#1_SARC.pdf`
- GitHub repository: `Reshwant-Borra/GNN_PCNA`
- Version 1 branch inspected through GitHub MCP: `project-version-1`
- Local ResearchOS/crawl context under `crawls/pcna-cryptic-pocket-gat-md-kb-final/`

## SARC Goal Captured

The SARC proposal frames the project as GNN-based residue-level discovery of candidate hidden PCNA binding sites, with AOH1996/8GLA as a required positive-control recovery check and MD as a test of whether predicted sites show dynamic or interface-relevant behavior. The governance docs preserve that direction but make the claims stricter: AOH1996 recovery is not proof of novel-site validity, and MD tests hypotheses rather than confirming the desired story.

## V1 Lessons Captured

Version 1 established useful infrastructure and limitations, but it also exposed Phase 2 risks:

- 8GLA/AOH1996 can become leakage if used for tuning and then reported as independent validation.
- C-alpha ligand-proximity labels must not be described as curated cryptic-pocket labels.
- PCNA asymmetric-unit handling and chain mapping can distort trimer biology.
- Chain ID, residue index, graph size, and batch-level aggregation can create shortcut learning.
- AUROC can look strong while AUPRC, top-k recovery, calibration, seed variance, or biological realism remain weak.
- ANM/MD-looking evidence must not be overinterpreted as proof of binding, mechanism, druggability, or therapeutic relevance.

## Files Created

| File | Purpose |
|---|---|
| `docs/scientific_governance/00_README.md` | Index, reading order, V1 risk summary, minimum required files before training/claims/MD |
| `01_SOURCE_OF_TRUTH.md` | Canonical repo, dataset, split, context, results, stale artifact rules |
| `02_ASSUMPTION_REGISTRY.md` | Structured assumptions and example PCNA/MD/evaluation assumptions |
| `03_FAILURE_MODE_CATALOG.md` | Full catalog of leakage, shortcut, MD, claim, and agent failure modes |
| `04_DATASET_CONSTRAINTS.md` | Dataset registry, inclusion/exclusion, chain, ligand, normalization constraints |
| `05_SPLIT_PROTOCOL.md` | Leakage-resistant split rules and split audit outputs |
| `06_LABELING_RULES.md` | Residue label definitions, bad labels, provenance, and audits |
| `07_PREPROCESSING_AND_GRAPH_RULES.md` | Structure preprocessing, graph metadata, feature, and cache rules |
| `08_MODEL_ARCHITECTURE_CONSTRAINTS.md` | Batch safety, logits, shortcut features, ablations |
| `09_EVALUATION_PROTOCOL.md` | Metrics, test-once rule, seeds, CIs, calibration, top-k |
| `10_BASELINE_REQUIREMENTS.md` | PocketMiner, fpocket, P2Rank, simple baselines, ablations |
| `11_BIOLOGICAL_REALISM_RULES.md` | Accessibility, conservation, trimer integrity, literature consistency |
| `12_PCNA_SPECIFIC_CHECKS.md` | PCNA trimer, PIP-box/APIM, AOH1996, ATX-101, claim language |
| `13_MD_VALIDATION_RULES.md` | MD pre-registration and unexpected/negative result interpretation |
| `14_CLAIM_POLICY.md` | Allowed and forbidden wording and claim audit |
| `15_PROVENANCE_AND_REPRODUCIBILITY.md` | Required hashes, commands, seeds, manifests |
| `16_CODING_AGENT_RULES.md` | Rules for Codex, Claude Code, and other coding agents |
| `17_RESEARCHOS_AGENT_RULES.md` | Multi-agent verification and ResearchOS uncertainty rules |
| `18_VERIFICATION_PIPELINE.md` | Gates before implementation, after data/training/prediction/MD/final writing |
| `19_STOP_CONDITIONS.md` | Mandatory pause triggers and remediation |
| `20_PHASE2_BUILD_CHECKLIST.md` | Stepwise Phase 2 build sequence and artifacts |
| `21_READINESS_GATE.md` | PASS/WARNING/FAIL readiness scoring |
| `22_UNEXPECTED_RESULTS_POLICY.md` | Scientific handling of surprising or negative outcomes |
| `23_FINAL_PROJECT_AUDIT_TEMPLATE.md` | Final audit sections and readiness decisions |

## How These Docs Prevent V1 Failures

- Dataset leakage is blocked by registry-first data handling, split-before-graph generation, sequence clustering, apo/holo grouping, and PCNA final-claim isolation.
- Bad split design is blocked by explicit unacceptable split types and split hashes required in every graph, checkpoint, and metric.
- Overclaims are blocked by allowed/forbidden claim language and claim-to-evidence auditing.
- Hallucinated biology is blocked by the assumption registry and coding/ResearchOS agent rules.
- Weak biological realism is blocked by accessibility, conservation, interface, trimer, and PCNA-specific audits.
- Stale artifacts are blocked by source-of-truth rules, manifests, and quarantine language.
- Wrong source of truth is blocked by canonical repo/dataset/split/context/results definitions.
- MD overinterpretation is blocked by pre-registration and a policy that MD is supportive, not definitive.
- Unexpected MD results are explicitly treated as evidence, not failure.
- Good metrics with invalid science are blocked by biological realism, baseline, calibration, seed, and provenance gates.
- Vibe coding is constrained by the required coding-agent prompt and fail-closed behavior.

## Remaining Open Questions

- Which exact Phase 2 dataset will become canonical: curated cryptic-pocket labels, ligand-proximity labels, PocketMiner/CryptoBench labels, or a separated multi-dataset setup?
- What sequence-identity threshold and structural-similarity method will be used for split grouping?
- Will 8GLA/AOH1996 be excluded from all tuning so it can serve as stronger held-out PCNA evidence, or explicitly remain only a positive-control sanity check?
- Which biological assembly policy will be used for PCNA trimer graphs and non-PCNA benchmark structures?
- Which MD systems, ligands, protonation states, replicate counts, and enhanced-sampling options are feasible before claims?

## Recommended Next Step

Before vibe coding continues, create the actual `DATASET_REGISTRY.md`, split assignment template, assumption registry entries, and a `reports/phase2/readiness_gate.md` instance. No training or scientific model edits should start until dataset, split, label, graph, and provenance readiness are PASS.
