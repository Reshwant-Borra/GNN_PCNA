# How to run the PCNA MD validation — every command, in order

This is a linear, copy-paste walkthrough for running the three MD stages
(0.1 ns smoke, 3 × 5 ns control-5, and the full 3×100/3×100 production
validation), including tmux usage. It complements
`md_validation_4070/CLOUD_MD_RUNBOOK.md`, which is the terser reference with
the full stage-gate rationale — this file is the "just tell me what to type"
version.

**Everything runs on the machine with the GPU.** Raw trajectories (`.dcd`
files) never need to be copied anywhere else. Only the final compact results
bundle (a small `.tar.gz`) is meant to be pushed to GitHub.

Run every command from the repository root (`GNN_PCNA/`) unless noted.

---

## 0. One-time setup

```bash
# Clone (skip if you already have the repo)
git clone https://github.com/Reshwant-Borra/GNN_PCNA.git
cd GNN_PCNA
git checkout presmoke-repair-20260816   # or main, once this branch is merged

# Environment
conda env create -f md_validation_4070/environment.yml
conda activate pcna-md-4070

# tmux (required — the launcher refuses to run MD outside tmux)
# Ubuntu/Debian:
sudo apt-get update && sudo apt-get install -y tmux
# macOS:
brew install tmux

# Sanity-check dependencies and GPU
python -c "import gemmi, mdtraj, openmm, pdbfixer, numpy, pandas, matplotlib; from scipy.spatial import ConvexHull; print('deps OK')"
nvidia-smi
```

Run the full precheck (this runs **no simulation**, it only checks your
environment, GPU, protocol hash, gate state, and the test suite):

```bash
./md.sh precheck
```

Check expected disk space and RAM for every stage before you start:

```bash
./md.sh estimates
```

---

## 1. Understanding tmux (if you haven't used it)

Every MD stage launches inside a **tmux session** so it keeps running even if
your SSH connection drops. You don't manage tmux directly — `md.sh` does it
for you — but you do need to know how to look at it and detach from it.

| What you want to do | Command |
|---|---|
| See what's running | `./md.sh status` or `tmux list-sessions` |
| Attach to the latest MD session | `./md.sh attach` |
| Attach to a specific session | `./md.sh attach pcna_smoke` |
| **Detach** (leave it running, return to your shell) | inside tmux: press `Ctrl-b`, release, then press `d` |
| Kill a session (rarely needed — prefer graceful stop, see §5) | `tmux kill-session -t pcna_smoke` |

You do **not** need to `tmux new` yourself — `./md.sh smoke`, `./md.sh
control5`, etc. create the session for you and print its name.

---

## 2. Stage 1 — Smoke test (0.1 ns, ~a few minutes)

Purpose: prove the whole pipeline (structure prep → solvate → minimize →
equilibrate → integrate → analyze) runs end-to-end on this machine before
committing to anything longer.

```bash
./md.sh smoke
```

This launches tmux session `pcna_smoke` and runs, inside it:
1. `run_md.py --run control --replicates 1 --ns 0.1 --md-stage smoke ...`
2. `analyze_md.py` (automatically, right after)

Watch it live:

```bash
./md.sh attach pcna_smoke
# Ctrl-b then d to detach and leave it running
```

Or just tail the log without attaching:

```bash
tail -f md_validation_4070/logs/smoke_*.log
```

Check status without attaching:

```bash
./md.sh status
```

When it's done, inspect what it actually produced (all real checks, not just
"did it finish"):

```bash
OUT=md_validation_4070/outputs

cat $OUT/8GLA/rep01/DONE.json
cat $OUT/8GLA/rep01/EQUILIBRATION.json      # temperature/density/energy/box-volume acceptance
cat $OUT/8GLA/rep01/MINIMIZATION.json       # did minimization actually resolve bad contacts?
cat $OUT/8GLA/prep/prep_audit.json          # 3 protein chains, rebuilt residues
cat $OUT/8GLA/storage_preflight.json
```

Quick pass/fail summary of the safety checks:

```bash
python - <<'PY'
import json, pathlib
d = json.loads(pathlib.Path("md_validation_4070/outputs/8GLA/rep01/DONE.json").read_text())
s = d["smoke_safety_checks"]
print("production_steps        :", d["production_steps"], "/", d["target_production_steps"])
print("minimization reduced PE :", s["minimization_reduced_potential_energy"])
print("catastrophic geometry   :", s["catastrophic_bond_or_geometry_failure"])
print("region mapping intact   :", s["candidate_region_mapping_integrity"]["all_candidate_residues_present"])
print("equilibration accepted  :", s["equilibration_acceptance"]["accepted"])
PY
```

Confirm the gate flipped to PASS:

```bash
./md.sh status
# gates:
#   smoke_0p1ns: PASS
```

**Stop here and actually look at the numbers above before continuing.**
Nothing advances automatically.

---

## 3. Stage 2 — Control-5 (3 × 5 ns 8GLA, ~hours depending on GPU)

Purpose: the real positive-control validation. Proves the analysis method can
actually detect pocket opening (not just recognize that 8GLA started open) by
demonstrating trajectory-derived dynamics (temporal autocorrelation +
spatial collectivity), not just a static difference.

```bash
./md.sh control5
```

Launches tmux session `pcna_control5` and runs, in order:
1. `run_md.py --run control --replicates 3 --ns 5 --md-stage control_validation`
2. `analyze_md.py`
3. `md_workflow.py control-report`

Same monitoring pattern as smoke:

```bash
./md.sh attach pcna_control5      # Ctrl-b d to detach
./md.sh status
tail -f md_validation_4070/logs/control5_*.log
```

When it's done, read the interpretability report:

```bash
cat md_validation_4070/CONTROL_INTERPRETABILITY_REPORT.md
cat md_validation_4070/outputs/analysis/REPORT.md
```

Look at the actual discriminator values per replicate:

```bash
python - <<'PY'
import json, pathlib
s = json.loads(pathlib.Path("md_validation_4070/outputs/analysis/summary.json").read_text())
g = s["control_interpretability_gate"]
print("gate   :", g["name"], g["status"])
print("reason :", g["reason"])
for r in g["per_replicate"]:
    print(f"\n{r['replicate']}  qualifies={r['qualifies']}  N={r['n_production_frames']}")
    print(f"  open-like fraction : {r['open_like_fraction']}")
    print(f"  pocket RMSF (nm)   : {r['pocket_rmsf_mean_nm']}")
    print(f"  D1 hull lag-1 ACF  : {r['D1_hull_lag1_autocorrelation']}  (must be >= {r['D1_iid_null_threshold']})")
    print(f"  D2 mean |DCCM|     : {r['D2_region_internal_mean_abs_dccm']}  (must be >= {r['D2_iid_null_threshold']})")
    for issue in r["issues"]:
        print("  ISSUE:", issue)
PY
```

**If this FAILS, that is a real result.** Do not tune thresholds, do not
re-run hoping for a different outcome, do not cherry-pick a replicate. A
failed control means the assay can't reliably see opening, and everything
downstream (production apo results) would be uninterpretable.

---

## 4. Gate 6 — human sign-off (manual, required before production)

Nothing in the code can grant this. You do it by hand, deliberately, after
actually reading the control-5 report above.

```bash
./md.sh gate6
# will say: Gate-6 approved : False, with the reason(s) why
```

To grant it:

```bash
cd md_validation_4070

COMMIT=$(git rev-parse HEAD)
CTRL=$(sha256sum CONTROL_INTERPRETABILITY_REPORT.md | awk '{print $1}')
PROTO=$(sha256sum FROZEN_MD_ANALYSIS_PROTOCOL.json | awk '{print $1}')
echo "commit=$COMMIT"
echo "control5_report_sha256=$CTRL"
echo "analysis_protocol_sha256=$PROTO"

cp GATE6_DECISION.template.json GATE6_DECISION.json
```

Now **edit `GATE6_DECISION.json` by hand** (any text editor) and fill in:

```json
{
  "schema_version": 1,
  "kind": "PCNA_MD_GATE6_DECISION",
  "approved": true,
  "approved_by": "<your name>",
  "approved_utc": "<output of: date -u +%Y-%m-%dT%H:%M:%SZ>",
  "commit": "<$COMMIT from above>",
  "control5_report_sha256": "<$CTRL from above>",
  "analysis_protocol_sha256": "<$PROTO from above>",
  "notes": "<what you reviewed and why production is authorized>"
}
```

Verify:

```bash
cd ..
./md.sh gate6
# Gate-6 approved : True
```

This file is gitignored — it must never be committed.

---

## 5. Optional — benchmark (performance only, not a scientific result)

```bash
./md.sh benchmark
cat md_validation_4070/BENCHMARK_REPORT.json
```

Tells you ns/day on this GPU so you can estimate wall-clock time for
production. It writes to a separate `benchmark_outputs/` directory and
cannot satisfy any scientific gate.

---

## 6. Stage 3 — Production (3 × 100 ns control + 3 × 100 ns apo)

This is the actual experiment. Only runs if Gate 6 is approved and control-5
passed.

```bash
./md.sh estimates    # confirm free disk space one more time
./md.sh production
```

This re-checks everything (Gate 6, control-5, protocol hash, CUDA, platform)
before writing a short-lived authorization token, then launches tmux session
`pcna_production` running:
1. `run_md.py --run control --replicates 3 --ns 100 --md-stage production ...`
2. `run_md.py --run apo --replicates 3 --ns 100 --md-stage production ...`
3. `analyze_md.py`

```bash
./md.sh attach pcna_production    # Ctrl-b d to detach
./md.sh status
```

**If your connection drops or the machine reboots**, just run the exact same
command again — every replicate resumes from its last checkpoint (every 10
ps) instead of restarting:

```bash
./md.sh production
```

Check resume history if you're curious:

```bash
cat md_validation_4070/outputs/8GLA/rep01/RESUME_AUDIT.json
cat md_validation_4070/outputs/8GLA/rep01/STATUS.json
```

---

## 7. Final analysis (runs automatically after production, or manually)

```bash
./md.sh analyze
```

This reads only files already on this machine — no trajectory ever needs to
leave it. Read the results:

```bash
cat md_validation_4070/outputs/analysis/REPORT.md
cat md_validation_4070/outputs/analysis/summary.json | python -m json.tool | less
column -s, -t < md_validation_4070/outputs/analysis/per_replicate.csv | less -S
```

---

## 8. Package compact results and push to GitHub

**Never push raw trajectories.** `./md.sh bundle` packages only the small
derived results (JSON/CSV/PNG/logs, no `.dcd`, no `.chk`, no solvated PDB)
into a single `.tar.gz`, with SHA-256 hashes of the excluded raw files so the
bundle stays traceable to trajectories that never moved.

```bash
./md.sh bundle
# writes md_validation_4070/pcna_md_results_<UTC-timestamp>.tar.gz

tar tzf md_validation_4070/pcna_md_results_*.tar.gz | head -30   # verify contents
du -h md_validation_4070/pcna_md_results_*.tar.gz                 # confirm it's small
```

### Push everything (code + this doc + compact results) to GitHub

```bash
git status --short
git add md_validation_4070/outputs/analysis/
git status --short              # double-check: NO .dcd, NO .chk, NO system_solvated.pdb listed
git add MD_HOWTO.md             # if this file changed
git commit -m "MD analysis results: <one line describing what the run showed>"
git push -u origin $(git branch --show-current)
```

If you only want the compact `.tar.gz` off the box without committing it to
git (e.g. to email it or drop it in shared storage):

```bash
# from your laptop
scp <user>@<cloud-host>:/path/to/GNN_PCNA/md_validation_4070/pcna_md_results_*.tar.gz .
```

---

## 9. Stopping things safely

```bash
# Ask a running replicate to stop cleanly — it checkpoints first, then exits.
tmux send-keys -t pcna_production C-c

./md.sh status                                       # confirm it shows RESUMABLE
cat md_validation_4070/outputs/8GLA/rep01/STATUS.json
```

- **Never `kill -9` a tmux session or the python process directly** — SIGINT
  (`C-c` inside tmux) and SIGTERM are handled and checkpoint first; a `-9`
  kill is not.
- **No command here ever deletes raw trajectories automatically.**
- If the machine is ephemeral (spot instance, etc.), copy
  `md_validation_4070/outputs/` to persistent storage before shutdown, or the
  checkpoints that make resuming possible are lost.

---

## Quick reference — every `./md.sh` command

```
./md.sh precheck    # environment + GPU + protocol + gate checks — no simulation
./md.sh estimates   # storage + RAM estimates for every stage
./md.sh smoke       # 0.1 ns 8GLA control smoke, in tmux
./md.sh control5    # 3 x 5 ns 8GLA control-first validation, in tmux
./md.sh benchmark   # short real-system CUDA benchmark, in tmux (PERFORMANCE_ONLY)
./md.sh gate6       # show Gate-6 decision state — never creates an approval
./md.sh production  # gated 3 x 100 ns control + 3 x 100 ns apo, in tmux
./md.sh analyze     # run the frozen analyzer on this machine
./md.sh bundle      # package ONLY compact derived results (no .dcd) as .tar.gz
./md.sh status      # summarize tmux sessions, runs, and gates
./md.sh attach [name]  # attach to the latest (or named) pcna_* tmux session
```

Stage order (nothing advances automatically past a failed or missing gate):

```
precheck → smoke → (you review) → control5 → (you review) → gate6 (manual)
        → benchmark (optional) → production → analyze → bundle → push
```
