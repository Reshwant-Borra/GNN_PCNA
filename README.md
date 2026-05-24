# GNN ResearchOS

Conservative autonomous research operating system for the GNN-PCNA + molecular-dynamics validation project. ResearchOS routes user requests to specialized agents, enforces scientific gates, tracks artifact provenance, and prevents claim drift. **No agent may approve its own work.**

The full design lives in `docs/`. The implementation lives in `research_os/`. Runtime state lives in `research_os_memory/`, `research_os_registries/`, and `reports/research_os/` (the last is git-ignored — regenerated on every run).

---

## For collaborators pulling this branch

1. Install once:
   ```bash
   pip install -e .
   pip install pytest
   ```
2. Confirm everything imports + tests pass:
   ```bash
   python -m pytest tests/ -q
   ```
   You should see `58 passed`.
3. Initialize / refresh your local runtime state:
   ```bash
   python -m research_os bootstrap
   ```
4. Run a full audit on the repo:
   ```bash
   python -m research_os audit
   ```
   The first run will block with the leakage gate at `not_started` and the validation gate at `fail`. That is **intentional** — the system refuses to let you proceed until the dataset, split protocol, and validation status are documented. See `STATUS.md` for the punch list.

---

## Quickstart

```bash
# Routing only — show which agents and gates a request would touch
python -m research_os route "Can we say MD validated the cryptic pocket?"

# Full audit workflow
python -m research_os audit

# Targeted workflows
python -m research_os training-eval
python -m research_os verify-metrics --metrics path/to/results.json
python -m research_os validate-md   --report path/to/md_report_dir
python -m research_os claim-audit   --paper path/to/manuscript.md
python -m research_os readiness     --paper path/to/manuscript.md

# Introspection
python -m research_os inspect-memory
python -m research_os inspect-registries
```

Every workflow writes a markdown + JSON report under `reports/research_os/<workflow>/<timestamp>/`.

---

## Design

Read `docs/README.md` first, then walk the numbered docs in order. The key non-negotiable rules:

- The Code Builder cannot approve its own code.
- The Model Training agent cannot approve its own metrics.
- The Paper agent cannot approve its own claims.
- The Validation agent cannot ignore contradictions.
- A headline metric is invalid until Leakage **and** Metrics agents approve.
- A biological claim is invalid until Biological Realism **and** Claim agents approve.
- A report, checkpoint, plot, or table is unsafe until Provenance records its inputs, command, commit, environment, and status.

## Status

See `STATUS.md` for what is done, what is partial, and what the human-in-the-loop owes the system before the project can move forward.
