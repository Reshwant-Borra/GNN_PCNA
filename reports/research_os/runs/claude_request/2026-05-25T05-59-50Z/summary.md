# Run summary — claude_request — 2026-05-25T05-59-50Z

## Routing

- Prompt: > Independently verify metrics in the repo.
- Decision: `unspecified`
- Confidence: `0.00`
- Risk: **high**
- Selected agents: context_source_truth, provenance_artifacts, contradiction_hunter, metrics_statistics, leakage_split, dataset_integrity, scientific_code_review, testing_environment, paper_claim
- Required gates: leakage, evaluation, dataset, code

## Result

- Blocked: **True**
- Block reason: paper_claim flagged a blocker: agent crashed: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list
- Human review required: **True**
  - provenance_artifacts: crash in provenance_artifacts: research_os_registries\artifact_registry.json is malformed; expected an object with an 'entries' list
  - contradiction_hunter: crash in contradiction_hunter: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list
  - metrics_statistics: crash in metrics_statistics: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list
  - paper_claim: crash in paper_claim: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list

### Gates
- `leakage` → **not_started**
- `evaluation` → **not_started**
- `dataset` → **not_started**
- `code` → **not_started**

### Agents
- `context_source_truth` → **warning** (conf 0.90): 9 of 9 canonical files present; 4 need review. git= branch= dirty=False.
- `provenance_artifacts` → **fail** (conf 0.00): agent crashed: research_os_registries\artifact_registry.json is malformed; expected an object with an 'entries' list
- `contradiction_hunter` → **fail** (conf 0.00): agent crashed: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list
- `metrics_statistics` → **fail** (conf 0.00): agent crashed: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list
- `leakage_split` → **blocked** (conf 0.90): Leakage gate cannot pass without a split protocol.
- `dataset_integrity` → **warning** (conf 0.80): Dataset registry audit: 0 missing, 5 pending.
- `scientific_code_review` → **pass** (conf 0.65): Scanned 0 Python files; 0 flagged; 0 findings.
- `testing_environment` → **warning** (conf 0.80): No tests/ directory; testing gate degraded.
- `paper_claim` → **fail** (conf 0.00): agent crashed: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list

## Files

- Transcript: `reports/research_os/runs/claude_request/2026-05-25T05-59-50Z/transcript.jsonl`
- Result JSON: `reports/research_os/runs/claude_request/2026-05-25T05-59-50Z/result.json`
