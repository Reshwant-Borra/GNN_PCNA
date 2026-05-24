# MVP Build Sequence

## MVP Scope

Build:

- Package skeleton.
- File-based memory loader.
- JSON registry loader/writer.
- Agent output schema validation.
- Router MVP.
- Context Agent MVP.
- Provenance basics.
- Contradiction basics.
- Claim audit basics.
- Full audit workflow skeleton.
- Tests.

Do not build full model retraining, cloud compute, literature crawling, paper generation, or MD execution first.

## Steps

1. Create package skeleton.
2. Define dataclasses for AgentOutput, Finding, Risk, GateUpdate, ArtifactEntry, ClaimEntry, ExperimentEntry, ContextPacket, OrchestrationPlan.
3. Implement registry load, validate, atomic write, append, update.
4. Implement memory loader and context packet builder.
5. Implement git/file/environment provenance helpers.
6. Implement rule-based router.
7. Implement Context Agent MVP.
8. Implement Claim Agent MVP.
9. Implement Contradiction Agent MVP.
10. Implement full audit skeleton.
11. Add tests.

## Router Test Prompts

- "Can we claim MD validated the cryptic pocket?"
- "Run training on the latest split."
- "What is the latest AUROC?"
- "Write the results section."
- "Make a pocket volume figure."
- "Check if our split leaks chains."
- "Review the metric script."
- "Run 100 ns MD on cloud."
- "What should my friend pull?"
- "Find hidden contradictions before submission."

## Done Criteria

- Package imports.
- Router tests pass.
- Memory loading works.
- Registries validate.
- Full audit skeleton runs.
- Reports are generated.
- No automation bypasses gates.
