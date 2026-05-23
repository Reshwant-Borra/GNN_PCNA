# MD Validation Analysis — Rishi's Runbook

Everything needed to run the full RMSF + DCCM + pocket volume validation on the 100ns trajectory.

---

## 1. File placement

Before running anything, confirm these files exist:

```
GNN_PCNA/
  data/md/
    1W60_production.dcd        ← 100ns trajectory (from cloud instance)
    1W60_solvated.pdb          ← topology (already in repo)     ✓
    1W60_fixed.pdb             ← fallback topology (already in repo)  ✓
  data/results/
    nma_apo_holo_comparison.json   ← ANM baseline (already in repo)  ✓
```

The DCD is the only file you need to supply. Everything else is already committed.

---

## 2. Dependencies

```bash
pip install MDAnalysis numpy scipy matplotlib
```

Or with conda:
```bash
conda install -c conda-forge mdanalysis numpy scipy matplotlib -y
```

Verify:
```bash
python -c "import MDAnalysis; import scipy; import matplotlib; print('all deps OK')"
```

No GPU needed — MDAnalysis runs on CPU only.

---

## 3. Run order (do these in sequence)

### Step 1 — Full MD analysis
```bash
cd GNN_PCNA

python scripts/run_md_analysis.py \
  --top  data/md/1W60_solvated.pdb \
  --traj data/md/1W60_production.dcd \
  --stride 10
```

**What it does:**
- Backbone-aligns the entire trajectory to frame 0 (MDAnalysis AlignTraj)
- Computes per-residue Cα RMSF over every 10th frame
- Computes Dynamic Cross-Correlation Matrix (DCCM) — two-pass covariance
- Estimates AOH1996 pocket volume per frame via Cα convex hull (scipy)

**Outputs written to `data/results/`:**
| File | Size | Contents |
|------|------|----------|
| `md_rmsf_1W60.json` | ~150 KB | per-residue RMSF, fold-change, n_frames, sim_time_ns |
| `md_dccm_1W60.npy` | ~1 MB | 510×510 float32 DCCM matrix |
| `md_pocket_volume.json` | ~500 KB | per-frame volume time series |
| `md_apo_comparison.json` | ~5 KB | summary: MD vs ANM comparison |

**Expected runtime:** 15–40 min on a modern CPU for a 100ns trajectory.

**Note on disk:** AlignTraj with `in_memory=False` writes a temporary aligned trajectory to disk.
Make sure you have ~50 GB free (trajectory size × 1.1).

---

### Step 2 — Generate figures
```bash
python scripts/make_md_figures.py --dpi 300
```

**Outputs written to `data/results/`:**
| File | Figure |
|------|--------|
| `fig4a_md_rmsf.png` | Per-residue RMSF bar chart, pocket residues in red |
| `fig4b_md_pocket_vol.png` | Pocket volume time series with rolling mean |
| `fig4c_md_dccm.png` | DCCM heatmap with AOH1996 pocket box in red |

---

### Step 3 — Rebuild paper with real numbers
```bash
python scripts/build_paper_docx.py
```

Output: `docs/GNN_PCNA_Research_Paper_v9_clean.docx`
The paper auto-populates section 3.8 with the actual RMSF, DCCM, and volume numbers.

---

## 4. How to interpret the results

### RMSF fold-change (the key number)
```
fold_change = pocket_rmsf / background_rmsf
```

| fold-change | Interpretation |
|-------------|----------------|
| > 1.1 | Pocket more flexible than background → MD supports cryptic opening |
| 0.9 – 1.1 | Neutral → check DCCM for correlated motion |
| < 0.9 | Pocket rigid in apo state → closed cryptic site (our preliminary 6.36ns result was 0.832) |

**ANM baseline (static, harmonic):** fold-change = 0.857 (apo 1W60)

The preliminary 6.36ns run gave fold-change = 0.832. The full 100ns run may differ —
longer timescales can reveal transient opening events not visible at 6ns.

### DCCM pocket-internal score
```
pocket_internal_dccm = mean off-diagonal correlation within AOH1996 residue block
```
- ANM apo baseline: 0.0995
- Preliminary MD (6.36ns): 0.3018
- Values > 0.3 indicate meaningful correlated motion at the pocket

### Volume
- Convex hull of Cα positions — overestimates true cavity volume
- Use for **relative changes over time**, not absolute pocket volume
- Transient spikes above baseline = partial opening events

---

## 5. Pocket residue definition

Both scripts use the identical AOH_GT set — 24 residues within 6Å of ZQZ in 8GLA chain A:

```python
AOH_GT = {25,26,27,38,39,40,41,42,44,45,46,47,
          123,125,126,128,231,232,233,234,250,251,252,253}
```

Sub-regions:
- **N-face loop:** 25–27
- **Front-face groove:** 38–47 (minus 43)
- **IDCL:** 123–128 (minus 124, 127)
- **C-terminal tail:** 231–234, 250–253

---

## 6. Push results back to GitHub

```bash
git add data/results/md_rmsf_1W60.json \
        data/results/md_apo_comparison.json \
        data/results/md_pocket_volume.json \
        data/results/md_dccm_1W60.npy \
        data/results/fig4a_md_rmsf.png \
        data/results/fig4b_md_pocket_vol.png \
        data/results/fig4c_md_dccm.png \
        docs/

git commit -m "feat: 100ns MD results — fold-change X.XXX, pocket RMSF X.XXX A"
git push origin main
```

Do NOT commit the DCD file (44 GB, will break git).

---

## 7. Sanity checks before pushing

```bash
python -c "
import json, numpy as np
rmsf = json.loads(open('data/results/md_rmsf_1W60.json').read())
comp = json.loads(open('data/results/md_apo_comparison.json').read())
dccm = np.load('data/results/md_dccm_1W60.npy')

print(f'Frames:       {rmsf[\"n_frames\"]}')
print(f'Sim time:     {rmsf[\"sim_time_ns\"]:.1f} ns')
print(f'Pocket RMSF:  {rmsf[\"pocket_rmsf_angstrom\"]:.3f} A')
print(f'BG RMSF:      {rmsf[\"background_rmsf_angstrom\"]:.3f} A')
print(f'Fold-change:  {rmsf[\"fold_change_pocket_vs_bg\"]:.3f}')
print(f'DCCM shape:   {dccm.shape}')
print(f'DCCM range:   [{dccm.min():.3f}, {dccm.max():.3f}]  (must be within [-1, 1])')
print(f'Pocket DCCM:  {comp[\"md_dccm\"][\"pocket_internal\"]:.4f}')
print()
fc = rmsf['fold_change_pocket_vs_bg']
if fc > 1.1:   print('>>> POSITIVE: pocket more flexible than background')
elif fc < 0.9: print('>>> RIGID: pocket closed in apo state (consistent with cryptic site)')
else:          print('>>> NEUTRAL: check DCCM and volume time series')
"
```

---

## 8. If the topology doesn't match the trajectory

If MDAnalysis raises a frame/atom count mismatch, try the alternative topology:

```bash
python scripts/run_md_analysis.py \
  --top  data/md/1W60_fixed.pdb \
  --traj data/md/1W60_production.dcd \
  --stride 10
```

The DCD was generated from `1W60_solvated.pdb` (with water + ions).
If the DCD is already stripped to protein-only, use `1W60_fixed.pdb`.
Check atom count: the DCD header reports n_atoms; the PDB must match.
