# Run summary — claude_request — 2026-05-25T06-00-00Z

## Routing

- Prompt: > audit the dataset for leakage
- Decision: `keyword_only`
- Confidence: `0.00`
- Risk: **high**
- Reason: Ollama unavailable or returned no result; deterministic keyword routing used.
- Selected agents: context_source_truth, leakage_split, dataset_integrity, metrics_statistics, preprocessing_auditor, contradiction_hunter
- Required gates: dataset, leakage
- Requires Claude fallback: **yes**

## Result

- Blocked: **True**
- Block reason: contradiction_hunter flagged a blocker: agent crashed: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list
- Human review required: **True**
  - metrics_statistics: crash in metrics_statistics: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list
  - preprocessing_auditor: crash in preprocessing_auditor: research_os_registries\artifact_registry.json is malformed; expected an object with an 'entries' list
  - contradiction_hunter: crash in contradiction_hunter: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list

### Gates
- `dataset` → **not_started**
- `leakage` → **not_started**

### Agents
- `context_source_truth` → **warning** (conf 0.90): 9 of 9 canonical files present; 4 need review. git=6efbaf4 branch=agents dirty=True.
- `leakage_split` → **blocked** (conf 0.90): Leakage gate cannot pass without a split protocol.
- `dataset_integrity` → **warning** (conf 0.80): Dataset registry audit: 0 missing, 5 pending.
- `metrics_statistics` → **fail** (conf 0.00): agent crashed: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list
- `preprocessing_auditor` → **fail** (conf 0.00): agent crashed: research_os_registries\artifact_registry.json is malformed; expected an object with an 'entries' list
- `contradiction_hunter` → **fail** (conf 0.00): agent crashed: research_os_registries\claim_registry.json is malformed; expected an object with an 'entries' list

## Files

- Transcript: `reports/research_os/runs/claude_request/2026-05-25T06-00-00Z/transcript.jsonl`
- Result JSON: `reports/research_os/runs/claude_request/2026-05-25T06-00-00Z/result.json`
