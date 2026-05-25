# Routing Guide

Last updated: 2026-05-25T00:00:00Z
Updated by: research_os.bootstrap
Status: current

Reference table mapping prompt **categories** to **expected agent selection**. Used by the Ollama semantic router as few-shot prompting context, and by humans / tests to validate routing decisions. When you add a new intent or change agent selection rules, mirror the change here.

> **Routing principle.** A prompt can match multiple categories (compound intent). The router should produce the **union** of all matching agents, deduplicated, with `context_source_truth` first. For high/critical risk, append `contradiction_hunter` at the end.

---

## Category: Literature / external research

Prompts asking about prior work, papers, surveys, benchmarks, PubMed/arXiv, "research how X works", "what's the literature on Y".

**Always include:** `context_source_truth`, `literature_web`, `document_knowledge_ingestion`, `provenance_artifacts`

**Do NOT include** (unless the prompt also explicitly asks for them): `validation_skeptic`, `model_training`, `code_builder`, `compute_planning`. Mentioning "cryptic pockets" or "MD simulation" as a *topic of literature* does NOT make this an MD validation task.

**Example prompts and expected agents:**

- "Research how Graph Neural Networks work and find PubMed articles on this topic"
  → `context_source_truth, literature_web, document_knowledge_ingestion, provenance_artifacts`
- "What's the recent literature on cryptic pockets?"
  → `context_source_truth, literature_web, document_knowledge_ingestion, provenance_artifacts`
- "find recent papers on cryptic pockets"
  → `context_source_truth, literature_web, document_knowledge_ingestion, provenance_artifacts`
- "survey of MD simulation methods for protein flexibility"
  → `context_source_truth, literature_web, document_knowledge_ingestion, provenance_artifacts`
- "what does prior work say about apo/holo leakage?"
  → `context_source_truth, literature_web, leakage_split, provenance_artifacts`
- "ingest these PubMed abstracts"
  → `context_source_truth, document_knowledge_ingestion, literature_web, provenance_artifacts`

**Compound case:** if the prompt also asks for a claim or paper section, add `paper_claim, biological_realism, contradiction_hunter`. ("Find papers on X and update the related work" is compound — include `paper_claim`.)

---

## Category: MD / validation

Prompts about molecular dynamics, RMSD/RMSF/DCCM, pockets, cryptic-pocket claims, trajectory interpretation.

**Always include:** `context_source_truth, validation_skeptic, biological_realism, metrics_statistics, provenance_artifacts`. For "validated/proves" wording, also `contradiction_hunter, paper_claim`.

**Example prompts:**

- "did MD validate the cryptic pocket?" (HIGH RISK — claim upgrade)
  → `context_source_truth, validation_skeptic, biological_realism, paper_claim, contradiction_hunter, metrics_statistics, provenance_artifacts`
  → `requires_human_approval: true` (claim upgrade above moderately_supported)
- "interpret the RMSF trajectory"
  → `context_source_truth, validation_skeptic, biological_realism, metrics_statistics, provenance_artifacts`
- "MD analysis of pocket flexibility"
  → `context_source_truth, validation_skeptic, biological_realism, metrics_statistics, provenance_artifacts`

---

## Category: Data leakage / splits

Prompts about train/test split, homology, apo/holo, chain leakage, cross-validation correctness.

**Always include:** `context_source_truth, leakage_split, dataset_integrity, preprocessing_auditor, metrics_statistics`

**Example prompts:**

- "is there data leakage in the split?"
  → `context_source_truth, leakage_split, dataset_integrity, preprocessing_auditor, metrics_statistics`
- "did we homology-block the train/test split?"
  → `context_source_truth, leakage_split, dataset_integrity, metrics_statistics`
- "apo/holo leakage check"
  → `context_source_truth, leakage_split, dataset_integrity, provenance_artifacts`

---

## Category: Claims / paper writing

Prompts about claims, papers, abstracts, results section, "validated", "confirmed".

**Always include:** `context_source_truth, paper_claim, metrics_statistics, validation_skeptic, biological_realism, provenance_artifacts, contradiction_hunter, reviewer_collaboration`

**Example prompts:**

- "audit the paper claims" (CRITICAL RISK)
  → `context_source_truth, paper_claim, metrics_statistics, validation_skeptic, biological_realism, provenance_artifacts, contradiction_hunter, reviewer_collaboration`
- "write the results section"
  → same as above + `visual_evidence`
- "can we say MD validated the cryptic pocket?" (CRITICAL RISK)
  → same as above + `requires_human_approval: true`

---

## Category: Metrics / numerical verification

Prompts mentioning AUROC, AUPRC, F1, MCC, precision/recall, accuracy, enrichment, confidence intervals.

**Always include:** `context_source_truth, metrics_statistics, leakage_split, provenance_artifacts, contradiction_hunter`

**Example prompts:**

- "verify the AUROC"
  → `context_source_truth, metrics_statistics, leakage_split, provenance_artifacts, contradiction_hunter`
- "compute AUPRC with confidence intervals"
  → same
- "do the precision/recall numbers hold up?"
  → same

---

## Category: Dataset audit

Prompts about dataset, PDB, labels, ground truth, residues, positives/negatives.

**Always include:** `context_source_truth, dataset_integrity, preprocessing_auditor, leakage_split`

---

## Category: Code / refactor / build

Prompts about implementing, building, refactoring, fixing bugs, writing scripts/tests/modules.

**Always include:** `context_source_truth, code_builder, scientific_code_review, testing_environment, provenance_artifacts`

For code review without mutation: drop `code_builder`.

---

## Category: Training / fine-tuning

Prompts about train, retrain, fine-tune, checkpoint, epoch.

**Always include:** `context_source_truth, leakage_split, dataset_integrity, preprocessing_auditor, model_training, metrics_statistics, provenance_artifacts`

---

## Category: Figures / visualization

Prompts about figure, plot, chart, heatmap, render.

**Always include:** `context_source_truth, visual_evidence, metrics_statistics, paper_claim, provenance_artifacts`

---

## Category: Submission readiness

Prompts about submit, submission, ready, preprint, publish, release, ship, handoff.

**Always include:** ALL agents in the submission readiness chain (`context_source_truth, provenance_artifacts, leakage_split, preprocessing_auditor, metrics_statistics, biological_realism, validation_skeptic, paper_claim, visual_evidence, reviewer_collaboration, testing_environment, contradiction_hunter`).

**Always set:** `requires_human_approval: true`. Submission is a Level-4 PI decision.

---

## Category: Compute planning

Prompts about GPU, cloud, budget, cost, runtime, schedule.

**Always include:** `context_source_truth, compute_planning, validation_skeptic`

Expensive runs (>4 GPU-hours or any cloud cost) → `requires_human_approval: true`.

---

## Category: Source of truth / status / debug

Prompts asking "what is X", "current Y", "latest", "show me", "summary", "status", "what's the latest checkpoint", "what blockers are open", "why did X fail".

**Always include:** `context_source_truth`. For debug ("why did X fail"): also `provenance_artifacts`.

**Do NOT include** (unless the prompt explicitly asks for them): `model_training`, `code_builder`, `paper_claim`, `leakage_split`, `dataset_integrity`, `preprocessing_auditor`. "What's the latest checkpoint?" is a STATUS query, NOT a training task — never select `model_training` for it. Risk level is LOW or MEDIUM, never high.

**Example prompts:**
- "what's the latest checkpoint?" → `context_source_truth` (optional: `provenance_artifacts`). risk=low.
- "show me current project status" → `context_source_truth`. risk=low.
- "what blockers are open?" → `context_source_truth` (optional: `contradiction_hunter`). risk=low.
- "why did the last training run fail?" → `context_source_truth, provenance_artifacts` (optional: `testing_environment, contradiction_hunter`). risk=medium.

---

## Category: Collaboration / sync

Prompts about pulling from branches, syncing with teammates, handoff.

**Always include:** `context_source_truth, reviewer_collaboration, provenance_artifacts`

---

## Compound intent examples

The router should produce the **union** of agents across all matched categories.

| Prompt | Categories matched | Selected agents |
|---|---|---|
| "Research how GNNs work and find PubMed articles on this topic" | literature | `context_source_truth, literature_web, document_knowledge_ingestion, provenance_artifacts` |
| "Train the model for 50 epochs and verify the AUROC" | training, metrics | `context_source_truth, leakage_split, dataset_integrity, preprocessing_auditor, model_training, metrics_statistics, provenance_artifacts, contradiction_hunter` |
| "Write the discussion section based on MD results" | claim, MD | full claim+MD chain + `paper_claim, visual_evidence` |
| "Audit the leakage and figure out if the AUROC is real" | leakage, metrics | `context_source_truth, leakage_split, dataset_integrity, preprocessing_auditor, metrics_statistics, provenance_artifacts, contradiction_hunter` |
| "Find papers on cryptic pockets and update the related work section" | literature, claim | `context_source_truth, literature_web, document_knowledge_ingestion, paper_claim, biological_realism, contradiction_hunter, reviewer_collaboration, provenance_artifacts` |

---

## Risky-request handling

Set `requires_human_approval: true` and `risk_level: critical` for any prompt that:

- Upgrades a claim above `moderately_supported`
- Submits / publishes / releases / preprints
- Triggers expensive compute (>4 GPU-hours or cloud cost)
- Modifies the canonical train/test split or dataset definition
- Deletes or overwrites an artifact
- Asserts "validated" / "confirmed" / "proves" without explicit MD/experimental evidence classification

The semantic router should mark these prompts even if confidence is high — they always need PI signoff.

---

## Confidence and fallback thresholds

- `confidence >= 0.75` → route as-is.
- `0.55 <= confidence < 0.75` → route as-is but set `requires_claude_fallback: true` so Claude Code can sanity-check.
- `confidence < 0.55` → route deterministically via keyword fallback and set `requires_claude_fallback: true`.
- `risk_level in ("high", "critical")` → always set `requires_claude_fallback: true`.
- Any prompt mentioning scientific claims, publication, validation, or expensive compute → set `requires_claude_fallback: true`.
