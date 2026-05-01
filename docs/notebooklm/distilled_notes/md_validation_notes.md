# MD Validation Methods — Distilled Notes

**Source:** paper_notes.md + needs NotebookLM extraction from MD literature
**Status:** Partially populated

---

## RMSF (from paper_notes.md)

- Measures per-residue positional fluctuation over trajectory
- MDAnalysis: `MDAnalysis.analysis.rms.RMSF(atomgroup).run()`
- Cryptic pocket signature: RMSF > 1.5–2.0 Å vs ~0.5–1.0 Å background
- Caveat: high RMSF ≠ pocket opening

---

## DCCM (from paper_notes.md)

- NxN symmetric matrix, values in [-1, 1]
- `C_ij = <Δr_i · Δr_j> / sqrt(<Δr_i²><Δr_j²>)`
- Pocket signature: high internal correlation + anti-correlation with gate residues
- Can compute via MDAnalysis or Bio3D (R)

---

## Volume Tracking (from paper_notes.md)

- Tool: fpocket / MDpocket (fpocket on trajectory)
- Command: `mdpocket --trajectory_file traj.xtc --trajectory_format xtc -f topology.pdb`
- Threshold: volume > 100 Å³ transiently = cryptic pocket evidence

---

## PCA of MD Trajectory (from paper_notes.md)

- Project trajectory onto PCs to identify collective motions
- PC1 often separates open/closed states
- If pocket-open state is on PC1: enhanced sampling along PC1 could accelerate

---

## Enhanced Sampling

- If 100 ns MD doesn't show pocket opening: consider metadynamics or REMD
- Toolchain: PLUMED + GROMACS
- Collective variable: pocket volume or inter-gate residue distance

---

## Needs NotebookLM Extraction

- [ ] Any published MD studies of PCNA IDCL dynamics
- [ ] Published RMSF thresholds for cryptic pockets (systematic reference)
- [ ] MDpocket citation + validation metrics
- [ ] Any PCNA conformational states described in literature

---

## Merge Target

→ Update `docs/knowledge/VALIDATION.md` after NLM extraction
