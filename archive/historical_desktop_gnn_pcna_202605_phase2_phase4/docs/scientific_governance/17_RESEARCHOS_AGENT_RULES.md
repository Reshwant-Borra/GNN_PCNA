# ResearchOS Agent Rules

## Purpose

Prevent ResearchOS agents from producing fake confidence, keyword-based biology, or claim-ready language without verification.

## Hard Rules

- Evidence must be source-linked.
- Inference must be labeled as inference.
- No single ResearchOS agent can approve a claim alone.
- Weak or contradictory evidence must trigger critic-planner review.

## ResearchOS Agents Must

- cite sources or point to a source index
- distinguish evidence from inference
- report uncertainty
- not pass biological realism based on keywords
- not use one agent as final authority
- run multi-agent verification
- escalate weak evidence
- trigger critic-planner feedback when gaps are found

## ResearchOS Agents Must Not

- produce fake confidence
- summarize without verification
- treat source count as source quality
- collapse unexpected results into failure
- produce claim-ready language without claim audit

## Forbidden Actions

- Treating source count as evidence strength.
- Passing biological realism because a keyword appears in an abstract.
- Collapsing negative or unexpected results into "failure."

## Required Multi-Agent Verification Flow

1. Source agent identifies primary sources and source-index entries.
2. Biology agent extracts PCNA-specific constraints.
3. Dataset/evaluation agent checks leakage, labels, splits, and metrics.
4. MD agent checks simulation interpretation policy.
5. Critic agent lists contradictions, weak evidence, and overclaims.
6. Planner agent converts verified findings into actionable gates.
7. Human or designated reviewer resolves unresolved scientific calls.

## Required Checks

- Source-quality check.
- Evidence-versus-inference check.
- Contradiction check.
- Claim-policy check.

## When To Replan

- Evidence contradicts the current implementation plan.
- A source is relevant but not decisive.
- A required assumption is missing.
- A result is unexpected.
- A baseline or biological audit conflicts with the GNN story.

## When To Stop

- Claim exceeds evidence.
- Source of truth is unclear.
- Leakage or label uncertainty is found.
- MD interpretation is being forced.
- ResearchOS cannot distinguish evidence from inference.

## When To Ask For Human Review

- PCNA mechanism interpretation.
- AOH1996/ATX-101 claim framing.
- Whether a site overlapping PIP-box/APIM is "known" or "candidate".
- Whether weak or conflicting evidence can support a claim.

## Prevention

Require a critic response and planner revision before any ResearchOS output becomes implementation guidance.

## Examples Of Failure

- ResearchOS says "many sources support PCNA druggability" without identifying which evidence supports the predicted site.
- ResearchOS treats no pocket opening in MD as failed simulation.
- ResearchOS writes final claim language before [14_CLAIM_POLICY.md](14_CLAIM_POLICY.md) audit.

## Compliance Artifact

`reports/phase2/researchos_verification_report.md`.

## If The Rule Fails

Discard the ResearchOS conclusion as advisory only, re-run with critic-planner flow, and require human review for claims.
