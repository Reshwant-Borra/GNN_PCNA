# Claim Audit Prompt

```text
Audit the provided text for scientific claims.

For each claim:
1. Extract the claim.
2. Map it to a claim ID if possible.
3. Classify claim strength.
4. Check whether registry allows the wording.
5. Check whether evidence supports the exact statement.
6. Identify disallowed wording.
7. Provide safe replacement wording.
8. Mark whether human approval is required.

Special caution:
- Do not allow "validated cryptic pocket" unless validation registry supports that exact claim.
- Do not allow "confirmed novel residues" without independent evidence.
- Do not allow broad generalization from tiny or leaky test sets.
- Do not allow MD stability to be described as pocket-opening validation.
```
