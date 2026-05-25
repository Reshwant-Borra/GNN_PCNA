# Registry Schemas

## Registry Files

```text
artifact_registry.json
claim_registry.json
experiment_registry.json
issue_registry.json
source_registry.json
environment_registry.json
decision_registry.json
```

## Shared Fields

Every entry should include:

- Stable ID.
- Created timestamp.
- Updated timestamp.
- Status.
- Created by.
- Evidence/provenance references.
- Notes.

Suggested IDs:

- `ART-0001`
- `CLAIM-0001`
- `EXP-0001`
- `ISSUE-0001`
- `SRC-0001`
- `ENV-0001`
- `DEC-0001`

## Status Values

Artifacts:

- `pending`
- `current`
- `stale`
- `invalid`
- `superseded`
- `draft`
- `archived`

Claims:

- `proven_experimentally`
- `strongly_supported_computationally`
- `moderately_supported`
- `suggestive`
- `hypothesis_generating`
- `unsupported`
- `contradicted`
- `deprecated`

Experiments:

- `planned`
- `approved`
- `running`
- `completed`
- `failed`
- `invalid`
- `superseded`

Issues:

- `open`
- `investigating`
- `fixed`
- `wont_fix`
- `superseded`

## Atomic Write Rule

Registry writes should:

1. Write temp JSON.
2. Validate.
3. Rename temp file to target.

Do not destructively delete entries; use statuses.
