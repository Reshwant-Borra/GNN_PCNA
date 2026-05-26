# Run summary — claude_request — 2026-05-25T18-50-56Z

## Routing

- Prompt: > Project setup and verification audit for GNN-PCNA. Use the following local documents as context: C:\Users\reshw\Downloads\AUDIT_2026-05-25.md and C:\Users\reshw\Downloads\DOCUMENTS_GNN\BORRA_#1_SARC.pdf. The project aim from BORRA_#1_SARC.pdf is: identify cryptic/allosteric bindi
- Decision: `semantic`
- Confidence: `0.95`
- Risk: **critical**
- Reason: Comprehensive project setup audit with data leakage, MD validation, and claims governance requirements; needs PI signoff
- Selected agents: context_source_truth, research_design, dataset_integrity, leakage_split, compute_planning, visual_evidence, reviewer_collaboration, model_training, validation_skeptic, biological_realism, contradiction_hunter, document_knowledge_ingestion, paper_claim, metrics_statistics, provenance_artifacts, preprocessing_auditor, scientific_code_review, testing_environment
- Required gates: claim, evaluation, validation, dataset, leakage, preprocessing, code
- Requires Claude fallback: **yes**
- Suggested workflow: `phase_2_blueprint`

## Result

- Blocked: **True**
- Block reason: biological_realism flagged a blocker: Biological realism audit: 1 findings, 0 claims weakened.
- Human review required: **True**
  - dataset or split protocol changes require PI approval

### Gates
- `claim` → **not_started**
- `evaluation` → **not_started**
- `validation` → **warning**
- `dataset` → **not_started**
- `leakage` → **not_started**
- `preprocessing` → **not_started**
- `code` → **not_started**
- `research_design` → **warning**
- `figure` → **pass**

### Agents
- `context_source_truth` → **warning** (conf 0.90): 9 of 9 canonical files present; 4 need review. git=b6078a5 branch=agents dirty=True.
- `research_design` → **warning** (conf 0.70): Research design audit: 6 findings.
- `dataset_integrity` → **warning** (conf 0.80): Dataset registry audit: 0 missing, 5 pending.
- `leakage_split` → **blocked** (conf 0.90): Leakage gate cannot pass without a split protocol.
- `compute_planning` → **pass** (conf 0.80): Compute planning audit: 0 findings.
- `visual_evidence` → **pass** (conf 0.60): Figure audit: 0 files on disk, 0 unregistered.
- `reviewer_collaboration` → **pass** (conf 0.80): Reviewer simulation: 12 canonical questions, 10 open risks tracked.
- `model_training` → **warning** (conf 0.70): Model training audit: 1 findings.
- `validation_skeptic` → **pass** (conf 0.80): Validation classification: Claim; 0 findings.
- `biological_realism` → **warning** (conf 0.75): Biological realism audit: 1 findings, 0 claims weakened.
- `contradiction_hunter` → **pass** (conf 0.85): Contradiction sweep produced 0 findings.
- `document_knowledge_ingestion` → **pass** (conf 0.80): Document ingestion integration: ingest_script=present, sources_registered=1.
- `paper_claim` → **pass** (conf 0.80): Paper/Claim audit: scanned 0 draft files; 0 findings.
- `metrics_statistics` → **pass** (conf 0.75): Metrics audit: scanned 0 files; 0 findings.
- `provenance_artifacts` → **warning** (conf 0.85): Reviewed 5 artifact entries; 1 provenance findings; 0 artifacts should be marked stale.
- `preprocessing_auditor` → **warning** (conf 0.75): Preprocessing audit found 1 issues among 0 graphs.
- `scientific_code_review` → **warning** (conf 0.65): Scanned 82 Python files; 11 flagged; 12 findings.
- `testing_environment` → **pass** (conf 0.80): Tests/ present; 0 findings; pytest_run=False.

## Files

- Transcript: `C:/Users/reshw/ResearchOS/reports/research_os/runs/claude_request/2026-05-25T18-50-56Z/transcript.jsonl`
- Result JSON: `C:/Users/reshw/ResearchOS/reports/research_os/runs/claude_request/2026-05-25T18-50-56Z/result.json`
