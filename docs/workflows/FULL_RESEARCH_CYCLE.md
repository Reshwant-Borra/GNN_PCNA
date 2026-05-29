# Full Research Cycle Workflow

## Trigger

Run when the user gives a new research task, asks what to do next, asks if results are valid, or wants to move to a new stage.

## Steps

1. User gives idea or task.
2. Orchestrator classifies intent and risk.
3. Context Agent summarizes source of truth.
4. Research Design checks hypothesis and roadmap.
5. Literature Agent gathers missing background if needed.
6. Dataset Agent checks data assumptions.
7. Leakage Agent validates split if metrics are involved.
8. Preprocessing Agent audits transformations if graphs/features/labels are involved.
9. Code Builder implements if needed.
10. Scientific Code Review audits code.
11. Testing Agent verifies environment and tests.
12. Model Agent trains/evaluates if needed.
13. Metrics Agent independently verifies results.
14. Biological Realism checks plausibility.
15. Validation Agent classifies validation evidence.
16. Contradiction Agent hunts conflicts.
17. Provenance Agent records outputs.
18. Claim Agent updates safe wording.
19. Figure Agent creates/audits visuals.
20. Reviewer Agent simulates criticism.
21. Orchestrator decides next step or asks human.

## Blocking Conditions

Block if:

- Required source-of-truth missing.
- Human approval required.
- Leakage Gate fails for metric claims.
- Preprocessing Gate fails for model results.
- Evaluation Gate fails for headline metrics.
- Validation Gate fails for validation claims.
- Claim Gate fails for paper writing.
- Critical tests skip.
