# PCNA frozen-GNN → MD: cloud runbook

**Everything below runs on the cloud GPU instance.** The raw trajectories stay there. No step
requires copying a DCD to another machine.

Read the stage gates first. Nothing advances automatically past a failed gate, and two
transitions are deliberately manual: smoke → control5, and control5 → Gate 6.

```
PRECHECK → SMOKE → SMOKE_REVIEW → CONTROL5 → CONTROL_INTERPRETATION → HUMAN_GATE6
        → BENCHMARK → PRODUCTION → ANALYSIS → FINAL_INTERPRETATION
```

| Transition | Automatic? |
|---|---|
| PRECHECK → SMOKE | no — you run `./md.sh smoke` |
| SMOKE → SMOKE_REVIEW | yes — smoke runs the analyzer itself |
| SMOKE_REVIEW → CONTROL5 | **NO. Never automatic.** You inspect artifacts, then run `./md.sh control5` |
| CONTROL5 → CONTROL_INTERPRETATION | yes — control5 runs analyze + control-report |
| CONTROL_INTERPRETATION → HUMAN_GATE6 | **NO. Never automatic.** A human writes `GATE6_DECISION.json` |
| HUMAN_GATE6 → PRODUCTION | no — you run `./md.sh production`, which re-checks every gate |
| PRODUCTION → ANALYSIS | yes — only if every replicate is complete and valid |
| ANALYSIS → FINAL_INTERPRETATION | no — human reads the report |

---

## A. Clone the exact commit

```bash
git clone https://github.com/Reshwant-Borra/GNN_PCNA.git
cd GNN_PCNA
git fetch origin
git checkout <COMMIT_SHA_FROM_THE_REPAIR_REPORT>
git rev-parse HEAD
git status --short
git branch --show-current
```

Record all three outputs before doing anything else.

## B. Environment

```bash
# Miniforge/conda must already be installed.
conda env create -f md_validation_4070/environment.yml
conda activate pcna-md-4070

# scipy is REQUIRED, not optional: the convex-hull openness metric fails closed without it.
python -c "import gemmi, mdtraj, openmm, pdbfixer, numpy, pandas, matplotlib; from scipy.spatial import ConvexHull; print('deps OK')"

sudo apt-get update && sudo apt-get install -y tmux
```

If you use a venv instead of conda, point the launcher at it:

```bash
export PCNA_MD_PYTHON=/absolute/path/to/python
```

## C. GPU verification

```bash
nvidia-smi
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

python - <<'PY'
import openmm as mm
names = [mm.Platform.getPlatform(i).getName() for i in range(mm.Platform.getNumPlatforms())]
print("openmm:", mm.version.version)
print("platforms:", names)
print("CUDA available:", "CUDA" in names)
PY
```

Any CUDA GPU with enough memory works: 4070, 4090, L4, L40S, A100, H100, B200. The scientific
parameters are identical on all of them — hardware changes speed, not methodology.

Multi-GPU box? Pick a device without changing any scientific parameter:

```bash
export OPENMM_CUDA_DEVICE_INDEX=0     # or pass --cuda-device-index 0 to run_md.py
```

## D. Repository / preflight checks — runs no simulation

```bash
./md.sh precheck
./md.sh estimates          # storage + analysis-RAM for every stage
./md.sh gate6              # must print "Gate-6 approved : False"
python -m pytest tests/ -q
```

`./md.sh precheck` verifies python, dependencies, OpenMM platforms, the GPU, the frozen
analysis-protocol hash, the current gate states, and runs the test suite. It simulates nothing.

Storage: `./md.sh estimates` prints the required free space per stage with a 1.5× safety
factor. At ~100k atoms the full ladder needs roughly **21 GiB free**. Confirm before smoke.

## E. Smoke — 0.1 ns 8GLA control

```bash
./md.sh smoke
```

Runs `run_md.py --run control --replicates 1 --ns 0.1 --md-stage smoke --equil-report-ps 2
--equil-dcd-ps 20`, then the analyzer, inside tmux session `pcna_smoke`.

## F. Attach / detach / status

```bash
./md.sh attach              # attaches the newest pcna_* session
./md.sh attach pcna_smoke   # or name it
# detach: Ctrl-b then d

./md.sh status
tmux list-sessions
tail -f md_validation_4070/logs/smoke_*.log
```

## G. Smoke artifact inspection

```bash
OUT=md_validation_4070/outputs

cat  $OUT/8GLA/rep01/DONE.json
cat  $OUT/8GLA/rep01/EQUILIBRATION.json     # frozen equilibration acceptance criteria
cat  $OUT/8GLA/rep01/MINIMIZATION.json      # 8GLA's high pre-minimization energy resolving
cat  $OUT/8GLA/rep01/PROVENANCE.json        # GPU name, driver, OpenMM version, seeds, hashes
cat  $OUT/8GLA/prep/prep_audit.json         # 3 chains, rebuilt residues
cat  $OUT/8GLA/storage_preflight.json
head -3 $OUT/8GLA/rep01/equilibration.log
ls -la $OUT/8GLA/rep01/
```

Check specifically:

```bash
python - <<'PY'
import json, pathlib
d = json.loads(pathlib.Path("md_validation_4070/outputs/8GLA/rep01/DONE.json").read_text())
s = d["smoke_safety_checks"]
print("production_steps        :", d["production_steps"], "/", d["target_production_steps"])
print("minimization reduced PE :", s["minimization_reduced_potential_energy"])
print("  initial PE            :", s["initial_potential_kj_mol"])
print("  minimized PE          :", s["final_minimized_potential_kj_mol"])
print("catastrophic geometry   :", s["catastrophic_bond_or_geometry_failure"])
print("  max bond length (nm)  :", s["bond_geometry_check"]["max_bond_length_nm"])
print("region mapping intact   :", s["candidate_region_mapping_integrity"]["all_candidate_residues_present"])
print("  missing residues      :", s["candidate_region_mapping_integrity"]["missing_residues"])
print("equilibration accepted  :", s["equilibration_acceptance"]["accepted"])
print("  failures              :", s["equilibration_acceptance"].get("failures"))
PY
```

8GLA's pre-minimization energy is expected to be very high (50 rebuilt residues at 3.77 Å).
That is not disqualifying **provided minimization resolves it** — which is exactly what
`minimization_reduced_potential_energy` and `catastrophic_bond_or_geometry_failure` report.

`./md.sh status` should now show `smoke_0p1ns: PASS`.

**STOP. Do not continue automatically.** Read the artifacts above first.

## H. Control-5 launch — 3 × 5 ns 8GLA

```bash
./md.sh control5
```

Runs `run_md.py --run control --replicates 3 --ns 5 --md-stage control_validation`, then
`analyze_md.py`, then `md_workflow.py control-report`, in tmux session `pcna_control5`.

## I. Control analysis

```bash
./md.sh status
cat md_validation_4070/CONTROL_INTERPRETABILITY_REPORT.md
cat md_validation_4070/outputs/analysis/REPORT.md

python - <<'PY'
import json, pathlib
s = json.loads(pathlib.Path("md_validation_4070/outputs/analysis/summary.json").read_text())
g = s["control_interpretability_gate"]
print("gate     :", g["name"], g["status"])
print("reason   :", g["reason"])
for r in g["per_replicate"]:
    print(f"\n  {r['replicate']}  qualifies={r['qualifies']}  N={r['n_production_frames']}")
    print(f"    open-like fraction : {r['open_like_fraction']}")
    print(f"    pocket RMSF (nm)   : {r['pocket_rmsf_mean_nm']}")
    print(f"    D1 hull lag-1 ACF  : {r['D1_hull_lag1_autocorrelation']}  (IID null >= {r['D1_iid_null_threshold']})")
    print(f"    D2 mean |DCCM|     : {r['D2_region_internal_mean_abs_dccm']}  (IID null >= {r['D2_iid_null_threshold']})")
    print(f"    static+noise null  : {r['static_noise_surrogate']}")
    for i in r["issues"]:
        print("    ISSUE:", i)
PY
```

D1 and D2 are the discriminators that make this a *dynamic* control rather than a
recognition that 8GLA started open. A static structure with per-frame coordinate noise fails
both by construction. The `static_noise_surrogate` line prints the matched null next to the
real value so you can see the separation directly.

**If the gate FAILS, that is a real result.** Do not tune thresholds. Do not re-run hoping for
a better outcome. A failed control means the assay cannot see opening, so an apo negative
would be uninterpretable.

## J. Gate-6 review — WITHOUT auto-approving

Nothing in this repository can approve Gate 6. `./md.sh production` will refuse until a human
creates the decision artifact.

```bash
./md.sh gate6        # shows exactly what is blocking
```

To grant it, **after** genuinely reviewing the control-5 report:

```bash
cd md_validation_4070

COMMIT=$(git rev-parse HEAD)
CTRL=$(sha256sum CONTROL_INTERPRETABILITY_REPORT.md | awk '{print $1}')
PROTO=$(sha256sum FROZEN_MD_ANALYSIS_PROTOCOL.json | awk '{print $1}')

cp GATE6_DECISION.template.json GATE6_DECISION.json
# Now EDIT GATE6_DECISION.json by hand:
#   approved                 -> true
#   approved_by              -> your name
#   approved_utc             -> date -u +%Y-%m-%dT%H:%M:%SZ
#   commit                   -> $COMMIT
#   control5_report_sha256   -> $CTRL
#   analysis_protocol_sha256 -> $PROTO
#   notes                    -> what you reviewed and why production is authorized
echo "commit=$COMMIT"; echo "control5=$CTRL"; echo "protocol=$PROTO"

cd ..
./md.sh gate6        # must now print "Gate-6 approved : True"
```

Gate 6 fails closed if the file is missing, malformed, `approved` is not boolean `true`, no
approver is named, the timestamp is unparseable or expired, or the commit / control-report /
protocol hashes do not match what is on disk. Changing the protocol or the code after approval
invalidates the approval rather than silently carrying it forward.

## K. Benchmark — PERFORMANCE_ONLY

```bash
./md.sh benchmark
cat md_validation_4070/BENCHMARK_REPORT.json
```

Uses the real PCNA system and the same integration setup, 0.02 ns, no equilibration. Override
with `PCNA_MD_BENCHMARK_NS=0.05 ./md.sh benchmark`.

**Benchmark output is `PERFORMANCE_ONLY` / `NOT_SCIENTIFIC_EVIDENCE`.** It writes to
`md_validation_4070/benchmark_outputs/`, a different directory from `outputs/`, so it can never
satisfy a scientific gate.

## L. Production — 3 × 100 ns control + 3 × 100 ns apo

```bash
./md.sh estimates        # confirm free space one more time
./md.sh production
```

`md_workflow.py production-gate` re-checks, in order: Gate-6 decision validity and binding →
control-5 pass → frozen protocol hash → not macOS → CUDA present → `scripts/md_readiness_gate.py`.
Only then does it write a short-lived authorization token that `run_md.py` must match exactly
(pocket, run role, replicate count, ns, outdir, platform, git commit, protocol hash).

Direct large-scale `run_md.py` invocation is refused. So are runs shaped to look small:
`1 × 500 ns`, `2 × 100 ns`, `2 × 1000 ns`, `6 × 99 ns`, and anything mislabelled
`--md-stage smoke` or `--md-stage diagnostic` that exceeds that stage's envelope.

## M. Production status / resume

```bash
./md.sh status
./md.sh attach pcna_production
```

Every replicate checkpoints every 10 ps. After a crash, reboot or preemption, **re-run the
exact same command** — each replicate resumes from its last checkpoint and never restarts:

```bash
./md.sh production
```

Inspect resume history:

```bash
cat md_validation_4070/outputs/8GLA/rep01/RESUME_AUDIT.json
cat md_validation_4070/outputs/8GLA/rep01/STATUS.json
```

## N. Final analysis — ON THE CLOUD INSTANCE

```bash
./md.sh analyze
```

This is the canonical analysis command. It reads, from this filesystem only:

```
outputs/<PDB>/system_solvated.pdb
outputs/<PDB>/rep*/production.dcd
outputs/<PDB>/rep*/{DONE,PROVENANCE,STATUS,EQUILIBRATION,MINIMIZATION}.json
outputs/<PDB>/rep*/{production,equilibration}.log
outputs/<PDB>/pocket_definition.json
md_validation_4070/pockets/final_consensus_1w60_20260815.json
md_validation_4070/FROZEN_MD_ANALYSIS_PROTOCOL.json
```

It loads the **protein atom subset only** (~1.1 GiB peak for 3 × 100 ns rather than ~8.9 GiB
if solvent were loaded), so it will not die after an expensive simulation succeeds.

Fail-closed by default: any replicate that is incomplete, truncated, has a `FAILED.json`, has
duplicate frames or log times, an inconsistent output interval, an unreadable log, or a
topology/role/pdb mismatch will abort the analysis rather than be silently dropped.

Diagnostics only (never for interpretation, and it cannot satisfy a gate):

```bash
python md_validation_4070/analyze_md.py --pocket final_consensus_1w60_20260815 \
  --outdir md_validation_4070/outputs --allow-incomplete-diagnostic
```

Read the results:

```bash
cat md_validation_4070/outputs/analysis/REPORT.md
cat md_validation_4070/outputs/analysis/summary.json | python -m json.tool | head -80
column -s, -t < md_validation_4070/outputs/analysis/per_replicate.csv | less -S
```

## O. Compact-result packaging

```bash
./md.sh bundle
```

Writes `md_validation_4070/pcna_md_results_<UTC>.tar.gz` containing only:

* `analysis/` — `summary.json`, `per_replicate.csv`, `REPORT.md`, `pocket_parity.json`,
  plots, `BUNDLE_MANIFEST.json`
* per-replicate `DONE/FAILED/STATUS/PROVENANCE/EQUILIBRATION/MINIMIZATION/RESUME_AUDIT.json`
* `production.log`, `equilibration.log`
* `pocket_definition.json`, `storage_preflight.json`, `prep_audit.json`

Explicitly excluded: `*.dcd`, `*.chk`, `*.npy`, `system_solvated.pdb`, `prepared_protein.pdb`.
Those stay here and are referenced by SHA-256 in `BUNDLE_MANIFEST.json`, so the compact bundle
remains traceable to trajectories that never moved.

```bash
tar tzf md_validation_4070/pcna_md_results_*.tar.gz | head -40
du -h md_validation_4070/pcna_md_results_*.tar.gz
```

Custom destination: `./md.sh bundle --bundle-out /tmp/results.tar.gz`.

## P. Optional push of compact results

```bash
git checkout -b md-results-$(date -u +%Y%m%d)
git add md_validation_4070/outputs/analysis/
git status --short              # verify: NO .dcd, NO .chk, NO system_solvated.pdb
git commit -m "MD analysis results: <one line on what the run showed>"
git push -u origin HEAD
```

`.gitignore` already excludes `md_validation_4070/outputs/`, so add the analysis directory
explicitly and check `git status --short` before committing. Trajectories must never be pushed.

Alternatively copy just the bundle off the box:

```bash
# run from your laptop
scp <user>@<cloud-host>:/path/to/GNN_PCNA/md_validation_4070/pcna_md_results_*.tar.gz .
```

## Q. Graceful shutdown

```bash
# Ask a run to stop cleanly: it checkpoints, writes STATUS.json RESUMABLE, and exits 130.
tmux send-keys -t pcna_production C-c

./md.sh status                  # confirm RESUMABLE, note the step count
cat md_validation_4070/outputs/8GLA/rep01/STATUS.json
```

Rules:

* **Never `kill -9` a running replicate.** SIGINT and SIGTERM are handled and checkpoint first.
* **Never delete raw trajectories.** No command in this repository deletes them automatically.
* Before terminating the instance, confirm every replicate is `COMPLETE` or `RESUMABLE`, run
  `./md.sh analyze` and `./md.sh bundle`, and copy the bundle off.
* If the instance is ephemeral, back up `md_validation_4070/outputs/` to persistent storage
  before shutdown — checkpoints are what make a resume possible.

```bash
# safe to run any time; resumes rather than restarts
./md.sh production
```
