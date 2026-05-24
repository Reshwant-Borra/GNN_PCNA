# PyMOL Render Notes

Status: current renders are checked in as-is for handoff.

The current PCNA PyMOL figures in `reports/figures/` are scientifically useful but not presentation-ready because residue text labels cover the structure and pocket region:

- `reports/figures/pcna_aoh1996_pocket_highlight.png`
- `reports/figures/pcna_8gla_holo_pocket.png`

The relevant render entrypoint is:

```bash
python scripts/render_pcna_pymol.py
```

It calls the per-structure PyMOL scripts under `scripts/pymol/`:

- `scripts/pymol/pcna_1w60_aoh_pocket.py`
- `scripts/pymol/pcna_8gla_holo_pocket.py`

The intended cleanup is to keep the pocket highlighting, ligand display, and protein orientation, but remove or greatly reduce the residue labels before producing final manuscript figures. The likely source of the clutter is the `cmd.label(...)` section near the end of each PyMOL script.

For final figures, render clean images without dense residue labels, then add any necessary callouts manually in a figure editor or with sparse PyMOL labels only for a few key residues.
