# Run summary — claude_request — 2026-05-26T14-17-39Z

## Routing

- Prompt: > Independently verify metrics in the repo.
- Decision: `unspecified`
- Confidence: `0.00`
- Risk: **high**
- Selected agents: context_source_truth, provenance_artifacts, contradiction_hunter, metrics_statistics, leakage_split, dataset_integrity, scientific_code_review, testing_environment, paper_claim
- Required gates: leakage, evaluation, dataset, code

## Result

- Blocked: **True**
- Block reason: leakage_split flagged a blocker: Leakage gate cannot pass without a split protocol.
- Human review required: **False**

### Gates
- `leakage` → **not_started**
- `evaluation` → **not_started**
- `dataset` → **not_started**
- `code` → **not_started**
- `claim` → **pass**

### Agents
- `context_source_truth` → **warning** (conf 0.90): 9 of 9 canonical files present; 4 need review. git= branch= dirty=False.
- `provenance_artifacts` → **warning** (conf 0.85): Reviewed 5 artifact entries; 1 provenance findings; 0 artifacts should be marked stale.
- `contradiction_hunter` → **pass** (conf 0.85): Contradiction sweep produced 0 findings.
- `metrics_statistics` → **pass** (conf 0.75): Metrics audit: scanned 0 files; 0 findings.
- `leakage_split` → **blocked** (conf 0.90): Leakage gate cannot pass without a split protocol.
- `dataset_integrity` → **warning** (conf 0.80): Dataset registry audit: 0 missing, 5 pending.
- `scientific_code_review` → **pass** (conf 0.65): Scanned 0 Python files; 0 flagged; 0 findings.
- `testing_environment` → **warning** (conf 0.80): No tests/ directory; testing gate degraded.
- `paper_claim` → **pass** (conf 0.80): Paper/Claim audit: scanned 0 draft files; 0 findings.

## Files

- Transcript: `reports/research_os/runs/claude_request/2026-05-26T14-17-39Z/transcript.jsonl`
- Result JSON: `reports/research_os/runs/claude_request/2026-05-26T14-17-39Z/result.json`
