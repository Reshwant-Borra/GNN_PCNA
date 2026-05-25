# Run summary — claude_request — 2026-05-25T18-41-50Z

## Routing

- Prompt: > Produce a concise literature-style research report on graph neural networks (GNNs). Include: (1) what GNNs are and why graphs need specialized neural architectures, (2) core message-passing formulation, (3) seminal and widely-used architectures such as spectral GCN/ChebNet, GCN, 
- Decision: `semantic`
- Confidence: `0.95`
- Risk: **high**
- Reason: compound: literature search + report generation on GNNs, including architecture, applications, limitations, and future directions, with provenance tracking
- Selected agents: context_source_truth, literature_web, document_knowledge_ingestion, paper_claim, biological_realism, contradiction_hunter, visual_evidence, metrics_statistics, leakage_split, dataset_integrity, provenance_artifacts
- Required gates: dataset, leakage
- Requires Claude fallback: **yes**
- Suggested workflow: `gnn_literature_review`

## Result

- Blocked: **True**
- Block reason: leakage_split flagged a blocker: Leakage gate cannot pass without a split protocol.
- Human review required: **True**
  - Semantic router flagged human approval.

### Gates
- `dataset` → **not_started**
- `leakage` → **not_started**
- `claim` → **pass**
- `figure` → **pass**
- `evaluation` → **pass**

### Agents
- `context_source_truth` → **warning** (conf 0.90): 9 of 9 canonical files present; 4 need review. git=ef953c4 branch=agents dirty=True.
- `literature_web` → **pass** (conf 0.60): Literature audit: 1 sources registered.
- `document_knowledge_ingestion` → **pass** (conf 0.80): Document ingestion integration: ingest_script=present, sources_registered=1.
- `paper_claim` → **pass** (conf 0.80): Paper/Claim audit: scanned 0 draft files; 0 findings.
- `biological_realism` → **warning** (conf 0.75): Biological realism audit: 1 findings, 0 claims weakened.
- `contradiction_hunter` → **pass** (conf 0.85): Contradiction sweep produced 0 findings.
- `visual_evidence` → **pass** (conf 0.60): Figure audit: 0 files on disk, 0 unregistered.
- `metrics_statistics` → **pass** (conf 0.75): Metrics audit: scanned 0 files; 0 findings.
- `leakage_split` → **blocked** (conf 0.90): Leakage gate cannot pass without a split protocol.
- `dataset_integrity` → **warning** (conf 0.80): Dataset registry audit: 0 missing, 5 pending.
- `provenance_artifacts` → **warning** (conf 0.85): Reviewed 5 artifact entries; 1 provenance findings; 0 artifacts should be marked stale.

## Files

- Transcript: `C:/Users/reshw/ResearchOS/reports/research_os/runs/claude_request/2026-05-25T18-41-50Z/transcript.jsonl`
- Result JSON: `C:/Users/reshw/ResearchOS/reports/research_os/runs/claude_request/2026-05-25T18-41-50Z/result.json`
