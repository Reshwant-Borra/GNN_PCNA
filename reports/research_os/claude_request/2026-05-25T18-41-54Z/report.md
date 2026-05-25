# ResearchOS - Claude Request

_Generated 2026-05-25T18-41-54Z_

## Request

> Produce a concise literature-style research report on graph neural networks (GNNs). Include: (1) what GNNs are and why graphs need specialized neural architectures, (2) core message-passing formulation, (3) seminal and widely-used architectures such as spectral GCN/ChebNet, GCN, 

- intents: ['split_or_leakage', 'document_ingestion', 'source_of_truth_query']
- risk level: **high**
- agents executed: context_source_truth, literature_web, document_knowledge_ingestion, paper_claim, biological_realism, contradiction_hunter, visual_evidence, metrics_statistics, leakage_split, dataset_integrity, provenance_artifacts
- gates evaluated: dataset, leakage

## Verdict

- blocked: **True**
- block reason: leakage_split flagged a blocker: Leakage gate cannot pass without a split protocol.
- human review required: **True**
  - Semantic router flagged human approval.

## Gate status

| Gate | Status |
| --- | --- |
| dataset | `not_started` |
| leakage | `not_started` |
| claim | `pass` |
| figure | `pass` |
| evaluation | `pass` |

## Agent outputs

### Context and Source-of-Truth

- status: **warning** (confidence 0.9)
- summary: 9 of 9 canonical files present; 4 need review. git=ef953c4 branch=agents dirty=True.
- findings: 5
  - **[MEDIUM]** DATASET_REGISTRY.md status=needs_review — _Have an authoritative agent refresh DATASET_REGISTRY.md and set status=current._
  - **[MEDIUM]** MODEL_REGISTRY.md status=needs_review — _Have an authoritative agent refresh MODEL_REGISTRY.md and set status=current._
  - **[MEDIUM]** COMPUTE_REGISTRY.md status=needs_review — _Have an authoritative agent refresh COMPUTE_REGISTRY.md and set status=current._
  - **[MEDIUM]** REVIEWER_RISK_REGISTER.md status=needs_review — _Have an authoritative agent refresh REVIEWER_RISK_REGISTER.md and set status=current._
  - **[LOW]** Working tree is dirty

### Deep Literature and Web Research

- status: **pass** (confidence 0.6)
- summary: Literature audit: 1 sources registered.

### Document and Knowledge Ingestion

- status: **pass** (confidence 0.8)
- summary: Document ingestion integration: ingest_script=present, sources_registered=1.

### Paper, Claim and Documentation

- status: **pass** (confidence 0.8)
- summary: Paper/Claim audit: scanned 0 draft files; 0 findings.
- gate updates: claim→pass

### Biological and Scientific Realism

- status: **warning** (confidence 0.75)
- summary: Biological realism audit: 1 findings, 0 claims weakened.
- findings: 1
  - **[CRITICAL]** Claim CLAIM-0004 is 'strongly_supported_computationally' with no evidence_for

### Contradiction and Error Hunter

- status: **pass** (confidence 0.85)
- summary: Contradiction sweep produced 0 findings.

### Visual Evidence and Figure

- status: **pass** (confidence 0.6)
- summary: Figure audit: 0 files on disk, 0 unregistered.
- gate updates: figure→pass

### Metrics, Statistics and Uncertainty

- status: **pass** (confidence 0.75)
- summary: Metrics audit: scanned 0 files; 0 findings.
- gate updates: evaluation→pass

### Leakage and Split Design

- status: **blocked** (confidence 0.9)
- summary: Leakage gate cannot pass without a split protocol.
- findings: 1
  - **[CRITICAL]** No documented split protocol — _Document chain-/homology-/apo-holo-blocked splits._
- gate updates: leakage→blocked

### Dataset and Label Integrity

- status: **warning** (confidence 0.8)
- summary: Dataset registry audit: 0 missing, 5 pending.
- findings: 5
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Datasets in use' still pending — _Replace 'pending' content with the actual definition._
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Label definition' still pending — _Replace 'pending' content with the actual definition._
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Missing-data policy' still pending — _Replace 'pending' content with the actual definition._
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Residue/chain mapping rules' still pending — _Replace 'pending' content with the actual definition._
  - **[MEDIUM]** DATASET_REGISTRY.md section 'Split protocol' still pending — _Replace 'pending' content with the actual definition._
- gate updates: dataset→warning

### Provenance, Versioning and Artifact

- status: **warning** (confidence 0.85)
- summary: Reviewed 5 artifact entries; 1 provenance findings; 0 artifacts should be marked stale.
- findings: 1
  - **[HIGH]** Artifact ART-0001 missing provenance fields: ['git_commit'] — _Update artifact ART-0001 with full provenance._

## Git state at report time

- branch: agents
- commit: ef953c4 (dirty)

## Workflow notes

This report was generated from a Claude Code conversational prompt. Claude should explain the structured result, blockers, gates, and next actions.
