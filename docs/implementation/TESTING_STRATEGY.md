# Testing Strategy

## Test Categories

### Unit Tests

- Schema validation.
- Registry load/save.
- Memory loading.
- Router classification.
- Gate resolution.
- Human escalation.
- Artifact stale propagation.
- Claim wording checks.

### Integration Tests

- Full audit on fixture repo.
- Claim audit against sample paper text.
- Metric verification on fixture predictions.
- Provenance record creation.
- Report writing.

### Scientific Guardrail Tests

Ensure the system blocks:

- Validation claims when validation is inconclusive.
- Headline metrics when Leakage Gate failed.
- Critical skipped tests being treated as success.
- Stale artifact in paper claim.
- Claim upgrade without human approval.
- Residue-level n as independent protein-level n.

## Critical Skip Policy

If PyTorch Geometric or another critical dependency is missing:

- Fresh environment workflow fails.
- Readiness workflow says not ready.
- Test report cannot say passed without caveat.

## Done Criteria

Tests must catch leakage, stale artifacts, inflated metrics, skipped critical tests, overstated claims, and unsupported MD validation.
