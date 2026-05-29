# Orchestrator Routing Specification

## Purpose

The Master Research Orchestrator must take arbitrary user or Claude Code conversation and automatically route it to the correct agents, gates, context, and human approval path.

It is the system's router, planner, gatekeeper, and conflict resolver.

## Required Behavior

For every request, the Orchestrator must:

1. Parse the request.
2. Identify intent.
3. Identify scientific risk.
4. Ask Context Agent for source-of-truth summary.
5. Determine required gates.
6. Select agents.
7. Build context packets.
8. Determine human approval requirements.
9. Execute, plan, block, or ask for approval.
10. Propose memory and registry updates only through the update protocol.

## Router Output

```json
{
  "request_summary": "",
  "intent": "",
  "risk_level": "low|medium|high|critical",
  "selected_agents": [],
  "required_gates": [],
  "context_packet": {
    "memory_files": [],
    "repo_files": [],
    "registries": [],
    "artifacts": []
  },
  "actions": [],
  "blocked": false,
  "block_reason": "",
  "human_review_required": false,
  "human_review_reason": "",
  "expected_outputs": []
}
```

## Intent Classes

| Intent | Meaning | Primary agents |
|---|---|---|
| `source_of_truth_query` | What is current/stale/valid | Context, Provenance, Contradiction |
| `research_design` | Hypothesis, roadmap, controls | Research Design, Literature, Biology |
| `data_audit` | PDBs, labels, chains, residues | Dataset, Preprocessing, Leakage |
| `split_or_leakage` | Splits, homology, leakage | Leakage, Dataset, Metrics |
| `preprocessing_audit` | Graphs, features, labels | Preprocessing, Dataset, Code Review |
| `code_build` | Implement or refactor | Code Builder, Code Review, Testing |
| `code_review` | Review code | Scientific Code Review, Testing |
| `training` | Train or tune models | Model Training, Leakage, Metrics, Provenance |
| `metric_verification` | AUROC/AUPRC/statistics | Metrics, Leakage, Provenance |
| `md_or_validation` | MD, RMSF, DCCM, volume | Validation, Biology, Metrics |
| `claim_or_paper` | Write or audit paper claims | Claim, Biology, Validation, Reviewer |
| `figure_generation` | Plots and figures | Visual Evidence, Metrics, Claim |
| `compute_planning` | GPU/cloud/MD runtime/cost | Compute Planning, Validation, Human |
| `submission_readiness` | Ready to submit/share | Reviewer, Claim, Testing, Provenance |
| `collaboration_sync` | Friend/repo handoff | Reviewer Collaboration, Context |
| `contradiction_hunt` | Find hidden problems | Contradiction plus relevant auditors |

## Routing Priority

Priority order:

1. Human approval or irreversible/expensive action.
2. Critical scientific integrity blocker.
3. Source-of-truth conflict.
4. Leakage or split issue.
5. Claim or paper issue.
6. Metric verification.
7. Validation or biological realism.
8. Code build or refactor.
9. Figure generation.
10. Collaboration summary.

## Trigger Examples

| User says | Route to |
|---|---|
| "Can we claim..." | Claim, Biology, Validation, Metrics, Contradiction |
| "Is this validated?" | Validation, Biology, Metrics, Provenance |
| "Run training" | Leakage, Model Training, Metrics, Provenance |
| "Latest AUROC" | Context, Provenance, Metrics, Leakage |
| "Write results section" | Claim, Metrics, Validation, Provenance, Reviewer |
| "Run MD" | Compute Planning, Validation, Human approval |
| "Find hidden problems" | Contradiction, Context, Provenance, Leakage, Metrics |

## Context Packet

Each selected agent receives:

- Task.
- Intent.
- Relevant memory files.
- Relevant registry entries.
- Relevant source/artifact files.
- Known risks.
- Allowed actions.
- Forbidden actions.
- Expected output schema.

Agents should not receive the full repo unless necessary.

## Human Escalation

Require human approval for:

- Expensive compute.
- Dataset/split protocol changes.
- Claim strength upgrades or major downgrades.
- Contradictory validation interpretation.
- Irreversible actions.
- Final figures.
- Submission.
- Agent disagreement on major conclusion.

## Example Blocker

```text
Blocked: paper writing should not proceed.

Reasons:
- The metric artifact is not independently verified.
- Leakage Gate is stale.
- MD evidence does not support validated cryptic-pocket wording.

Next required agents:
- Metrics, Statistics and Uncertainty.
- Leakage and Split Design.
- Validation and Skeptic.
- Paper, Claim and Documentation.
```

## Routing Pseudocode

```python
def route_request(message, memory, registries):
    intents = classify_intent(message)
    risk = classify_risk(message, intents)
    source_truth = context_agent.summarize(intents)
    gates = determine_required_gates(intents)
    agents = select_agents(intents, gates, risk)
    human = requires_human_review(message, intents, risk, source_truth)
    if has_blocking_gate_failure(gates, source_truth):
        return blocked_plan(intents, gates, agents, source_truth)
    return orchestration_plan(intents, agents, gates, human)
```
