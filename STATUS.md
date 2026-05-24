# ResearchOS — Implementation Status

_Last updated: 2026-05-24 — initial implementation pass._

This document tracks **what is built**, **what works end-to-end**, and **what is intentionally left for human / scientific work** that ResearchOS by design refuses to fabricate.

If you are pulling this for the first time, run:

```bash
pip install -e .
pip install pytest
python -m pytest tests/ -q       # expect: 58 passed
python -m research_os bootstrap
python -m research_os audit
```

The first audit will block. That is correct — see "Open items" below.

---

## What is built

### Package layout

```
research_os/
  __init__.py                  public API (Orchestrator, dataclasses)
  __main__.py                  CLI (10 subcommands)
  orchestrator.py              gate-enforcing runtime
  schemas/                     dataclasses + closed vocabularies
    core.py                    AgentOutput, Finding, Risk, EvidenceRef, GateUpdate, MemoryUpdate
    context.py                 ContextPacket, OrchestrationPlan
    gates.py                   GateName, GateStatus
    registries.py              ArtifactEntry, ClaimEntry, ExperimentEntry, IssueEntry,
                               SourceEntry, EnvironmentEntry, DecisionEntry
    vocab.py                   STATUSES, SEVERITIES, GATE_STATUSES, INTENT_CLASSES, …
  registries/
    store.py                   RegistryStore with atomic write + dup/vocab rejection
  memory/
    store.py                   MemoryStore + MemoryUpdateProposal + section-level
                               replacement + human-approval gating
  tools/
    git.py                     capture_git_state()
    hashing.py                 file_hash / directory_hash / text_hash
    environment.py             capture_environment() with pip freeze + CUDA
    dependency_graph.py        BFS stale propagation
    provenance.py              ProvenanceRecord bundle
  routing/
    intent.py                  17-intent rule-based classifier
    risk.py                    low/medium/high/critical
    agents.py                  intent → ordered agent list (context first, contradiction last)
    gates.py                   intent → required gates
    human.py                   regex + loose-phrase human-approval triggers
    context_builder.py         per-intent memory + registry projection
    router.py                  top-level Router
  agents/
    base.py                    BaseAgent, AgentContext, phrase_in_text helpers
    orchestrator_role.py       MasterResearchOrchestratorAgent
    context_provenance.py      ContextSourceTruth, Provenance, ContradictionHunter
    data_audit.py              Dataset, Leakage, Preprocessing, ScientificCodeReview, Testing
    science_evaluation.py      ResearchDesign, BiologicalRealism, Literature, Metrics,
                               ModelTraining, ComputePlanning, ValidationSkeptic
    communication.py           CodeBuilder, PaperClaim, VisualEvidence, ReviewerCollaboration
  workflows/
    runner.py                  shared workflow harness
    full_audit.py
    training_eval.py
    metric_verification.py
    md_validation.py
    claim_audit.py
    submission_readiness.py
  reports/
    writer.py                  markdown + JSON report writers

research_os_memory/            9 canonical markdown files (seeded)
research_os_registries/        7 JSON registries (atomic, sequential IDs)
reports/research_os/<wf>/<ts>/ workflow outputs (git-ignored, regenerated per run)

tests/                         58 tests
```

### Public API

```python
from research_os import Orchestrator, AgentOutput, ClaimEntry, ArtifactEntry, GateStatus

orch = Orchestrator(repo_root=".")
orch.bootstrap()
plan = orch.route("Can we say MD validated the cryptic pocket?")
result = orch.execute_plan(plan)
print(result.blocked, result.gate_status, result.human_review_reasons)
```

### CLI

| Command | Purpose |
| --- | --- |
| `route <msg>` | Show the orchestration plan as JSON (no execution). |
| `run <msg>` | Route + execute, print the full result JSON. |
| `audit` | Full repo audit (all 18 audit-class agents). |
| `training-eval` | Leakage-clean training/eval gate check. |
| `verify-metrics --metrics …` | Independent metric verification. |
| `validate-md --report …` | MD validation classification. |
| `claim-audit --paper …` | Paper / claim wording audit. |
| `readiness --paper …` | Submission readiness matrix + human signoff. |
| `bootstrap` | Create memory + registry files if missing. |
| `inspect-memory` | Show canonical file headers. |
| `inspect-registries` | Validate registries; report counts. |

### Tests (58 passing)

- `test_schemas.py` — closed-vocabulary validation, required fields, range checks.
- `test_registries.py` — atomic writes, sequential IDs, dup rejection, immutable fields.
- `test_memory.py` — initialization, safe updates, human-approval gating, target validation.
- `test_router.py` — 10 canonical prompt classifications + agent ordering + gate requirements + human escalation.
- `test_stale_propagation.py` — BFS marks downstream stale, never revives `invalid`.
- `test_orchestrator.py` — end-to-end: claim request blocks when validation inconclusive, submission requires human, contradiction hunter for high risk, current artifact with stale dependency flagged, no self-approval of claim gate.
- `test_scientific_guardrails.py` — leakage blocks without split protocol, leakage blocks metric artifacts with no split-artifact dependency, validation skeptic fails on inconclusive, biological realism flags strong claim without evidence, AUROC-without-AUPRC flagged, disallowed wording blocked, contradiction hunter flags strong-claim-vs-inconclusive-MD, scientific code review flags skipped tests, testing environment flags missing tests/.

### Conservative defaults enforced

- Validation defaults to `inconclusive` → validation gate `fail` until classified.
- Leakage gate refuses to pass without a documented split protocol.
- `requires_human_approval` memory updates are held in `pending_memory_updates`, never silently applied.
- Gate owners cannot self-approve their own gates — required reviewer agents must have run first.
- Disallowed paper phrases (`validated cryptic pocket`, `discovered binding site`, `MD validates`, …) caught with a loose phrase matcher that tolerates intervening articles.
- Metric artifacts without a `split` artifact dependency are flagged critical.
- Current artifacts whose dependencies are `stale` or `invalid` are flagged critical.

---

## What ResearchOS will not do for you (by design)

These are not "missing features." They are scientific decisions the system refuses to fabricate; a human (or downstream agent with real data) must fill them in. Until they are filled in, gates block downstream work.

| Gate | Why it currently fails | What you (the PI / collaborator) must do |
| --- | --- | --- |
| `dataset` | All 5 sections of `DATASET_REGISTRY.md` say "Pending …". | Document the PDBs, chains, label definition, missing-data policy, residue/chain numbering, and split protocol. |
| `leakage` | No split protocol → cannot enumerate chain / homology / apo-holo / label-transfer / feature-normalization leakage checks. | After `dataset` is filled, document the actual split (chain-blocked + homology-blocked + apo/holo separated + PDB held out + feature normalization split-scoped + label transfer audited). |
| `preprocessing` | No graph artifacts registered. | After data + split are settled, run preprocessing and register the graph artifacts (path, command, git commit, dataset hash, environment hash, dependencies). |
| `code` | No `tests/` for the GNN / MD pipeline itself; ResearchOS only ships its own tests. | Add tests under `tests/gnn/` and `tests/md/` covering preprocessing, training, evaluation, and MD analysis. |
| `evaluation` | No metric artifacts registered yet; AUROC-only metric files in the repo would be flagged. | Register metric artifacts with `dependencies=[<split_artifact_id>, <checkpoint_artifact_id>]` and always report AUPRC + the positive-class baseline + uncertainty alongside AUROC. |
| `validation` | Default classification is `inconclusive`. | Run the MD validation workflow and explicitly classify each MD piece of evidence as supports / partially supports / inconclusive / weakens / contradicts. |
| `claim` | `CURRENT_CLAIMS.md` has no accepted claims, and any disallowed wording in a paper draft is blocked. | Author claim entries via the claim registry with allowed/disallowed wording, evidence links, and limitations. |
| `figure` | Any figure file in the repo that is not registered as an artifact is flagged. | Register figures with their generating command, inputs, and the claim they support. |
| `research_design` | `PROJECT_CANONICAL_STATUS.md` is seeded; the recommended falsification / controls / baselines sections are still placeholder. | Tighten the falsifier language (e.g., "performance collapses under homology-clean split", "novel residues physically implausible", "MD fails to show pocket opening under tested apo conditions"). |
| `submission` | Composite of all above. | Re-run `python -m research_os readiness` after the other gates are documented. |

---

## Where the human is non-negotiably required

These trigger `human_review_required=True` from the router and cannot be auto-approved:

- Any wording variant of "MD validated …", "validated cryptic pocket", "confirmed novel residues", "discovered binding site", "experimentally validated", "proved", "MD proves opening" — even with intervening articles ("MD validated _the_ cryptic pocket").
- Final figures, final abstract, final manuscript, final paper.
- `submit`, `submission`, `preprint`, `publish`, `release`.
- ≥10 ns MD runs, cloud GPU runs, anything flagged "expensive" or "budget".
- Dataset / split protocol changes.
- Artifact deletion or trajectory removal.

When the router sets `human_review_required=True`, the workflow report lists the reason; the orchestrator does not advance without an explicit human decision recorded in `decision_registry.json` + `HUMAN_DECISIONS.md`.

---

## Known gaps and follow-ups (for future iterations)

These are real "code is not yet there" items, not gating decisions:

1. **Real metric reproduction.** The Metrics agent today reads metric JSONs and checks AUROC/AUPRC pairing + CI presence. It does *not* yet re-run predictions to independently reproduce the numbers. The hook is the agent's `notes["metric_files_seen"]`; a follow-up agent should load predictions + labels and recompute.
2. **Real MD analysis.** The Validation agent today reads the classification from `VALIDATION_STATUS.md`. The MD analysis (RMSD/RMSF/DCCM/pocket volume/contact persistence/opening frequency) is not yet automated — the existing GNN-PCNA MD notebooks need a thin wrapper that registers their outputs as artifacts.
3. **Live training trigger.** `ModelTrainingAgent` audits the model registry; it does not yet drive an actual training run. Wire the existing `colab_retrain.ipynb` / `pretrain.py` / `finetune.py` flows behind a `train` workflow with mandatory `LeakageGate.pass` + `PreprocessingGate.pass` pre-check.
4. **Literature crawler.** `LiteratureWebAgent` only counts entries in `source_registry.json`. Populating it from a real source (Semantic Scholar, OpenAlex) is a follow-up.
5. **Figure generation.** `VisualEvidenceAgent` audits but does not generate. Hook a Matplotlib/PyMOL render pipeline behind a `figures` workflow that registers outputs with provenance.
6. **Embedding / full-text memory search.** Per `docs/00_EXECUTIVE_BUILD_PLAN.md` Phase 6 — not in MVP scope.
7. **Cross-machine collaboration sync.** `ReviewerCollaborationAgent` produces the canonical reviewer-question list; cross-repo diff/sync (e.g., friend's branch state) is a follow-up.

None of these gaps degrade the conservative-safety guarantees: until they are filled in, the affected gates stay at `not_started` / `warning` / `fail`, and downstream work blocks.

---

## How to extend it

- **Add a new agent.** Subclass `research_os.agents.base.BaseAgent`, set `agent_id` + `display_name`, implement `run(packet) -> AgentOutput`, then register it in `research_os/agents/__init__.py::AGENT_REGISTRY` and wire its ID into `research_os/routing/agents.py::_AGENT_MAP`.
- **Add a new gate.** Add the name to `research_os/schemas/gates.py::GateName.ALL`, append it to the right intents in `research_os/routing/gates.py::_INTENT_GATES`, and decide which agent emits its `GateUpdate`.
- **Add a new intent.** Add to `research_os/schemas/vocab.py::INTENT_CLASSES`, then map keyword patterns in `research_os/routing/intent.py::_INTENT_PATTERNS` and recommended agents in `research_os/routing/agents.py`.
- **Add a workflow.** Create `research_os/workflows/<name>.py` that calls `run_workflow()` with the right intent list, then register it in `research_os/workflows/__init__.py::WORKFLOWS` and add a CLI subcommand in `research_os/__main__.py`.

---

## File counts

- 31 Python source files (~5,000 lines)
- 9 test files (~750 lines, 58 tests)
- 9 seeded canonical memory files
- 7 seeded JSON registry files
- 6 workflow runners
- 10 CLI subcommands
- 20 agents, all gated by `AgentOutput.validate()`

---

## Bottom line for the next person to pick this up

**ResearchOS is fully completed at the orchestration layer.** Schemas, registries, memory, routing, agents, gates, workflows, CLI, and tests all work and enforce the docs' non-negotiable rules.

**The project-scientific layer is empty by design.** The collaborator must:

1. Document the dataset + split protocol so the leakage gate can pass.
2. Register the actual graph / checkpoint / metric / MD / figure artifacts with full provenance.
3. Run the MD validation workflow and explicitly classify the evidence.
4. Curate the claim registry with allowed/disallowed wording before any paper writing.

Until those are done, every `audit` will (correctly) block. That is the system working as intended.
