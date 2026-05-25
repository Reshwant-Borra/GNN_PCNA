# Agent Registry

Last updated: 2026-05-25T00:00:00Z
Updated by: research_os.bootstrap
Status: current

Compact registry of every ResearchOS scientific agent. This file is the **primary input to the Ollama semantic router** — keep entries terse and the format stable. Each agent has the same fields so the router can extract them deterministically.

When you add or rename an agent in `research_os/agents/__init__.py:AGENT_REGISTRY`, mirror the change here.

---

### context_source_truth
- name: Context and Source of Truth
- purpose: Resolve the canonical state of the project before any other agent runs. Reads memory files and registries; never trusts repo source alone.
- when_to_use: ALWAYS. Every workflow starts with this agent. Use when the prompt asks "what is X", "current status", "summary", or any open-ended research question.
- when_not_to_use: Never skip. Even pure compute tasks (`figure_generation`) need source-of-truth context.
- example_prompts: "what is the latest checkpoint?", "current status", "summarize project state"
- keywords: latest, current, what is, status, summary, source of truth, show me
- required_gates: none
- typical_outputs: AgentOutput with `evidence_used` pointing at memory files
- risk_level: low
- related_agents: provenance_artifacts, contradiction_hunter
- workflows: full_audit, training_eval, md_validation, claim_audit, metric_verification, submission_readiness

### research_design
- name: Research Design and Falsification
- purpose: Audit research question, hypothesis, null hypothesis, falsifiers, controls, baselines in PROJECT_CANONICAL_STATUS.md.
- when_to_use: User asks about hypothesis, experiment design, roadmap, what-to-do-next, baselines.
- when_not_to_use: Pure compute task with no scientific framing.
- example_prompts: "what experiment should we run next?", "is the hypothesis falsifiable?", "design the next study"
- keywords: hypothesis, research question, falsifiable, null hypothesis, roadmap, experiment design, controls, baselines
- required_gates: research_design
- typical_outputs: Findings about missing/weak design fields; gate update on research_design
- risk_level: medium
- related_agents: biological_realism, literature_web, validation_skeptic
- workflows: full_audit, submission_readiness

### biological_realism
- name: Biological and Scientific Realism
- purpose: Block claims that violate basic biology (e.g. "MD validated the cryptic pocket"), enforce safe wording on claims registry, judge whether predicted residues / pockets / contacts are biologically plausible.
- when_to_use: Any claim audit, MD interpretation, paper draft review, validation discussion. Also for residue plausibility checks (e.g. "are predicted residues near known AOH1996 contacts?", "is this pocket region biologically plausible?", "do these residues make biological sense?").
- when_not_to_use: Pure data/code refactor with no claim attached. Pure literature search with no interpretation requested.
- example_prompts: "did MD prove pocket opening?", "is this claim biologically plausible?", "are the predicted residues near known AOH1996 contacts?", "is this pocket region biologically plausible?"
- keywords: biological, biology, plausible, realistic, MD, pocket, cryptic, validated, proves, residue, AOH1996, contact, binding site
- required_gates: validation
- typical_outputs: Downgrade claim strength; surface disallowed wording
- risk_level: high
- related_agents: validation_skeptic, paper_claim, contradiction_hunter
- workflows: full_audit, claim_audit, md_validation, submission_readiness

### literature_web
- name: Literature and Web Research
- purpose: Find prior work, citations, surveys, benchmarks, related papers. Pull from PubMed / arXiv / web. Maintain source_registry entries with provenance.
- when_to_use: User asks about prior work, literature, citations, papers, articles, PubMed, arXiv, surveys, benchmarks, "research how X works".
- when_not_to_use: User asks only about local artifacts or compute. Pure code refactor.
- example_prompts: "Research how Graph Neural Networks work and find PubMed articles on this topic", "find recent papers on cryptic pockets", "what does the literature say about apo/holo splits?", "survey of MD simulation methods", "benchmark papers for PCNA"
- keywords: literature, papers, articles, PubMed, arXiv, prior work, survey, review, citations, references, benchmark, related work, research how, find papers, scientific articles, journal, publication
- required_gates: none (but feeds research_design + claim gates)
- typical_outputs: Source registry entries (SRC-*); ingest report with hits and relevance
- risk_level: medium
- related_agents: document_knowledge_ingestion, research_design, context_source_truth
- workflows: full_audit, claim_audit, submission_readiness

### dataset_integrity
- name: Dataset Integrity
- purpose: Audit dataset versioning, label definition, missing-data policy, residue/chain mapping, ground-truth provenance.
- when_to_use: User mentions dataset, PDB, labels, ground truth, data quality, residues, positives/negatives, train/test data.
- when_not_to_use: Pure paper-claim review with no dataset reference.
- example_prompts: "audit the dataset", "are the labels right?", "what's the ground truth definition?"
- keywords: dataset, PDB, label, ground truth, data quality, residue, positives, negatives, schema
- required_gates: dataset
- typical_outputs: Dataset registry diff; integrity findings
- risk_level: high
- related_agents: leakage_split, preprocessing_auditor, provenance_artifacts
- workflows: full_audit, training_eval, submission_readiness

### leakage_split
- name: Leakage and Split Integrity
- purpose: Detect homology leakage, apo/holo leakage, chain leakage, train/test overlap, cross-validation correctness.
- when_to_use: User mentions split, leakage, train/test, cross-validation, homolog, apo/holo, chain leakage.
- when_not_to_use: No data/model context (e.g. pure literature query).
- example_prompts: "is there data leakage in the split?", "did we homology-block the train/test split?", "apo/holo leakage check"
- keywords: leakage, leak, split, train/test, cross-validation, homolog, apo/holo, chain leak, cv, k-fold
- required_gates: leakage
- typical_outputs: Leakage findings; split protocol audit
- risk_level: critical
- related_agents: dataset_integrity, metrics_statistics, provenance_artifacts
- workflows: full_audit, training_eval, metric_verification, submission_readiness

### preprocessing_auditor
- name: Preprocessing Auditor
- purpose: Audit graph construction, feature alignment, residue mapping, label alignment, normalization.
- when_to_use: User asks about preprocessing, graph construction, features, residue mapping, label alignment.
- when_not_to_use: Pure inference or paper-review context.
- example_prompts: "audit the preprocessing pipeline", "are features leaking labels?", "graph construction check"
- keywords: preprocess, graph construction, features, align, normalize, residue map, label align
- required_gates: preprocessing
- typical_outputs: Preprocessing findings; rebuild recommendations
- risk_level: high
- related_agents: dataset_integrity, scientific_code_review
- workflows: full_audit, training_eval, submission_readiness

### code_builder
- name: Code Builder and Refactor
- purpose: Plan or apply code changes (refactor, new module, bug fix). In audit context only proposes a patch plan.
- when_to_use: User asks to implement, build, refactor, write a script/module/tests, fix a bug.
- when_not_to_use: User wants only review, audit, or analysis (no mutation).
- example_prompts: "implement the loss function", "refactor the data loader", "fix the leakage bug"
- keywords: implement, build, refactor, write script, write tests, fix bug, create module, create cli
- required_gates: code
- typical_outputs: Patch plan; required reviewer list (scientific_code_review + testing_environment)
- risk_level: medium
- related_agents: scientific_code_review, testing_environment, provenance_artifacts
- workflows: full_audit

### scientific_code_review
- name: Scientific Code Review
- purpose: Review code for scientific correctness: leakage, off-by-one residue indices, train/test contamination, masking, loss function.
- when_to_use: User asks to review/audit code, especially data pipelines, training loops, evaluation scripts.
- when_not_to_use: Pure refactor that doesn't touch scientific logic.
- example_prompts: "review the training script", "audit the evaluation code"
- keywords: review code, code review, audit code, audit script, audit module
- required_gates: code
- typical_outputs: Code findings, gate update on code
- risk_level: high
- related_agents: code_builder, testing_environment, preprocessing_auditor
- workflows: full_audit, training_eval

### testing_environment
- name: Testing and Environment
- purpose: Verify reproducibility — environment pinning, seed control, deterministic flags, test coverage, CI status.
- when_to_use: User asks about reproducibility, environment, seeds, deterministic, tests, CI.
- when_not_to_use: Pure paper/claim review.
- example_prompts: "is the run reproducible?", "check the environment lock", "did tests pass?"
- keywords: reproduce, environment, seed, deterministic, tests, CI, pin, conda, requirements
- required_gates: code
- typical_outputs: Reproducibility findings
- risk_level: medium
- related_agents: scientific_code_review, provenance_artifacts
- workflows: full_audit, training_eval, submission_readiness

### model_training
- name: Model Training
- purpose: Track training history, checkpoints, hyperparameters; produce experiment_registry entries.
- when_to_use: User asks to ACTIVELY train, retrain, or fine-tune a model. Verbs like train/retrain/fine-tune/fit.
- when_not_to_use: Status queries about checkpoints ("what's the latest checkpoint?", "show me training history") — those are pure source-of-truth queries, NOT training tasks. Also skip for literature, code review, claims, and any non-training prompt.
- example_prompts: "train for 50 epochs", "fine-tune from checkpoint X", "retrain with new split"
- keywords: train, retrain, fine-tune, checkpoint, epoch, hyperparameters
- required_gates: evaluation
- typical_outputs: Experiment registry entry; training log artifact
- risk_level: high
- related_agents: metrics_statistics, leakage_split, provenance_artifacts
- workflows: training_eval, full_audit

### metrics_statistics
- name: Metrics and Statistics
- purpose: Recompute and verify AUROC/AUPRC/precision/recall/F1/MCC with confidence intervals; flag misuse of metrics.
- when_to_use: User mentions AUROC, AUPRC, precision, recall, F1, MCC, metric, accuracy, enrichment, confidence interval.
- when_not_to_use: Pure literature/preprocessing tasks.
- example_prompts: "verify the AUROC", "compute AUPRC with CI", "do the metrics hold up?"
- keywords: AUROC, AUPRC, precision, recall, F1, MCC, metric, accuracy, enrichment, confidence interval, verify metrics
- required_gates: evaluation
- typical_outputs: Verified metrics JSON; metrics findings
- risk_level: high
- related_agents: leakage_split, contradiction_hunter, provenance_artifacts
- workflows: metric_verification, training_eval, claim_audit, full_audit

### compute_planning
- name: Compute Planning
- purpose: Plan compute budget, GPU/cloud cost, runtime estimates for expensive runs (MD, large training).
- when_to_use: User asks about compute, GPU, cloud, budget, storage, cost, runtime, schedule.
- when_not_to_use: Pure analysis/review tasks.
- example_prompts: "plan the MD compute budget", "how much GPU time will training take?"
- keywords: compute, GPU, cloud, budget, storage, cost, runtime, schedule
- required_gates: none
- typical_outputs: Compute plan; expensive-run approval request
- risk_level: medium
- related_agents: validation_skeptic, model_training
- workflows: training_eval, md_validation

### validation_skeptic
- name: Validation Skeptic
- purpose: Classify MD evidence (supports/partial/inconclusive/weakens/contradicts) against the validation question. Block "validated" claims without explicit classification.
- when_to_use: User explicitly mentions MD trajectories, RMSD/RMSF/DCCM, OpenMM, or asks to interpret existing MD evidence ("did MD validate X?", "does MD support Y?").
- when_not_to_use: Literature queries that merely mention "cryptic pocket" or "MD" as a topic of papers ("find literature on cryptic pockets" is NOT a validation task). Pure status / source-of-truth queries. Pure paper-claim review that doesn't reference MD results.
- example_prompts: "did MD validate the pocket?", "RMSF analysis", "interpret the trajectories", "does MD support pocket opening?"
- keywords: MD, molecular dynamics, RMSD, RMSF, DCCM, validation, trajectory, OpenMM, pocket opening
- required_gates: validation
- typical_outputs: Validation classification; MD evidence findings
- risk_level: critical
- related_agents: biological_realism, metrics_statistics, provenance_artifacts
- workflows: md_validation, full_audit, claim_audit, submission_readiness

### contradiction_hunter
- name: Contradiction Hunter
- purpose: Find conflicts between claims, metrics, MD evidence, code, and prior decisions. Run last on high-risk pipelines.
- when_to_use: User asks to find bugs, contradictions, hidden issues, conflicts. Also auto-runs on high/critical risk.
- when_not_to_use: Trivial source-of-truth queries (still safe to run but adds latency).
- example_prompts: "find contradictions in the project", "look for hidden conflicts", "break the paper"
- keywords: contradict, hidden bug, conflict, find issue, break, sanity check
- required_gates: validation, claim
- typical_outputs: Contradiction findings; gate downgrades
- risk_level: critical
- related_agents: paper_claim, leakage_split, metrics_statistics
- workflows: claim_audit, metric_verification, full_audit, submission_readiness

### provenance_artifacts
- name: Provenance and Artifacts
- purpose: Audit artifact_registry — checkpoints, predictions, figures, trajectories. Detect stale/invalid artifacts; chain artifacts to source data + code commit.
- when_to_use: User asks about artifacts, provenance, checkpoints, figures, trajectories, data hashes, reproducibility chain.
- when_not_to_use: Pure literature/hypothesis discussions with no artifact.
- example_prompts: "is checkpoint X stale?", "verify the artifact provenance", "regenerate stale artifacts"
- keywords: artifact, provenance, checkpoint, figure, trajectory, hash, lineage, stale, regenerate
- required_gates: none
- typical_outputs: Artifact registry diff; staleness findings
- risk_level: high
- related_agents: dataset_integrity, model_training, visual_evidence
- workflows: full_audit, training_eval, submission_readiness

### paper_claim
- name: Paper, Claim and Documentation
- purpose: Audit paper drafts and CURRENT_CLAIMS.md for disallowed wording. Block paper writing if validation/claim/leakage gates aren't pass.
- when_to_use: User mentions claim, paper, manuscript, abstract, results section, draft, docs, "write the X section".
- when_not_to_use: Pure code refactor or compute task.
- example_prompts: "audit the paper", "is this claim safe to publish?", "write the results section"
- keywords: claim, validate, paper, manuscript, abstract, results section, write, draft, docs, say, describe
- required_gates: claim
- typical_outputs: Claim audit report; safe-wording replacements; gate update on claim
- risk_level: critical
- related_agents: biological_realism, validation_skeptic, contradiction_hunter, reviewer_collaboration
- workflows: claim_audit, full_audit, submission_readiness

### visual_evidence
- name: Visual Evidence and Figures
- purpose: Audit figures for misleading axes, missing CIs, cropped data, overclaim. Block submission if figure gate not pass.
- when_to_use: User mentions figure, plot, visualize, chart, heatmap, render.
- when_not_to_use: No figure context.
- example_prompts: "audit the figures", "regenerate figure 3", "is the heatmap honest?"
- keywords: figure, plot, visualize, chart, heatmap, render, axis, caption
- required_gates: figure
- typical_outputs: Figure findings; figure gate update
- risk_level: high
- related_agents: paper_claim, metrics_statistics
- workflows: full_audit, submission_readiness

### reviewer_collaboration
- name: Reviewer Collaboration
- purpose: Maintain REVIEWER_RISK_REGISTER.md, simulate reviewer questions/concerns/objections, track human collaborators, sync handoffs.
- when_to_use: ANY prompt that mentions "reviewer", "reviewers ask", "reviewer concerns", "simulate reviewers", or that prepares for peer review / submission. Also collaborator sync, branch pulls.
- when_not_to_use: Pure technical audits with no peer-review or collaboration framing.
- example_prompts: "what will reviewers ask?", "simulate reviewer concerns about the MD evidence", "simulate reviewer concerns on leakage", "prepare reviewer responses", "pull my friend's branch"
- keywords: reviewer, reviewers, reviewer concerns, simulate reviewers, peer review, collaborator, friend, pull branch, sync, teammate, handoff
- required_gates: none
- typical_outputs: Reviewer risk register update; sync plan
- risk_level: medium
- related_agents: paper_claim, contradiction_hunter
- workflows: submission_readiness, claim_audit

### document_knowledge_ingestion
- name: Document and Knowledge Ingestion (Agent 21)
- purpose: Ingest PDFs, papers, transcripts, notes, web pages into source_registry with provenance hashing and chunking.
- when_to_use: User wants to ingest, upload, add, index a source/paper/document/PDF/transcript/note. Also triggered by "research X" prompts where literature_web needs an ingestion target.
- when_not_to_use: User asks only for in-memory analysis with no new source.
- example_prompts: "ingest this PDF", "add the lab notebook transcripts", "index the protocol papers", "Research how Graph Neural Networks work and find PubMed articles on this topic"
- keywords: ingest, upload, add source, add paper, add document, add pdf, add transcript, add note, index, source registry, document ingestion, knowledge ingestion, agent 21
- required_gates: none
- typical_outputs: Source registry entries; ingest report
- risk_level: medium
- related_agents: literature_web, context_source_truth, provenance_artifacts
- workflows: full_audit, claim_audit

### master_orchestrator
- name: Master Research Orchestrator
- purpose: Top-level dispatcher. NOT directly invoked by intent — represents the orchestrator role in the graph view and in human-approval flows.
- when_to_use: Never select via routing. Surfaced by the dashboard as the center node and by the human-approval workflow.
- when_not_to_use: Don't ever add to selected_agents from the router.
- example_prompts: (none)
- keywords: orchestrator, master, dispatcher
- required_gates: none
- typical_outputs: Workflow-level summary; human approval requests
- risk_level: low
- related_agents: (all)
- workflows: (all — center role)

---

## Quick agent ID list (for router validation)

```
master_orchestrator, context_source_truth, research_design, biological_realism,
literature_web, dataset_integrity, leakage_split, preprocessing_auditor,
code_builder, scientific_code_review, testing_environment, model_training,
metrics_statistics, compute_planning, validation_skeptic, contradiction_hunter,
provenance_artifacts, paper_claim, visual_evidence, reviewer_collaboration,
document_knowledge_ingestion
```
