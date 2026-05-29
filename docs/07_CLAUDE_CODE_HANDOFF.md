# Claude Code Handoff

## First Files to Read

Claude Code should read:

1. `docs/research_os/README.md`
2. `docs/research_os/00_EXECUTIVE_BUILD_PLAN.md`
3. `docs/research_os/02_ORCHESTRATOR_ROUTING_SPEC.md`
4. `docs/research_os/memory/MEMORY_SYSTEM.md`
5. `docs/research_os/agents/00_AGENT_INDEX.md`
6. `docs/research_os/schemas/AGENT_OUTPUT_SCHEMA.md`
7. `docs/research_os/implementation/TARGET_REPO_STRUCTURE.md`
8. `docs/research_os/implementation/MVP_BUILD_SEQUENCE.md`

## Prime Directive

Build GNN ResearchOS as a conservative scientific review system. Do not optimize for impressive metrics. Optimize for source-of-truth integrity, leakage prevention, metric validity, biological realism, honest claims, provenance, and reviewer readiness.

## First Build Task

Build:

- `research_os/` package skeleton.
- Memory loader.
- Registry loader/writer.
- Agent output schemas.
- Router MVP.
- Context packet builder.
- Basic tests.

Do not build training automation, cloud compute, or paper generation first.

## Required Orchestrator Behavior

Example command:

```bash
python -m research_os.orchestrator "Can we say MD validated the GNN pocket?"
```

Expected route:

- Context.
- Validation.
- Biological Realism.
- Metrics.
- Claim.
- Contradiction.

Expected gate awareness:

- Validation Gate.
- Claim Gate.
- Provenance check.

Expected output if evidence is insufficient:

```json
{
  "blocked": true,
  "block_reason": "MD evidence does not currently support strong cryptic-pocket validation wording.",
  "human_review_required": true
}
```

## Tests Required

- Registry schema validation.
- Artifact stale propagation.
- Claim downgrade behavior.
- Router prompt tests.
- Human approval for compute and major claims.
- Gate failure blocking.
- Critical skipped tests treated as failure.

## Handoff Prompt

```text
Implement GNN ResearchOS from docs/research_os/.
Start with file-based memory, JSON registries, provenance helpers, orchestrator routing, context packet builder, gate status model, and tests.
Do not build model automation, MD execution, or paper writing until memory, provenance, routing, and gates work.
No agent may approve its own work.
```
