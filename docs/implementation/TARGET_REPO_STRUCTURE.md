# Target Repo Structure

## Python Package

```text
research_os/
  __init__.py
  __main__.py
  orchestrator.py
  agents/
    base.py
    context_source_truth.py
    research_design.py
    biological_realism.py
    literature_web.py
    dataset_integrity.py
    leakage_split.py
    preprocessing_auditor.py
    code_builder.py
    scientific_code_review.py
    testing_environment.py
    model_training.py
    metrics_statistics.py
    compute_planning.py
    validation_skeptic.py
    contradiction_error_hunter.py
    provenance_artifacts.py
    paper_claim_docs.py
    visual_evidence.py
    reviewer_collaboration.py
  memory/
  registries/
  routing/
  workflows/
  schemas/
  reports/
  tools/
```

## Runtime State

```text
research_os_memory/
research_os_registries/
reports/research_os/
```

## Recommended CLI

```bash
python -m research_os route "Can we claim MD validated the pocket?"
python -m research_os audit --repo .
python -m research_os verify-metrics --metrics data/results/test_split_eval.json
python -m research_os validate-md --report reports/md_validation_100ns_2026-05-23
python -m research_os claim-audit --paper manuscript_grc_final.md
python -m research_os readiness --paper manuscript_grc_final.md
```

## Implementation Rule

ResearchOS audits and orchestrates first. It may call training or MD scripts later, but it should not bypass gates.
