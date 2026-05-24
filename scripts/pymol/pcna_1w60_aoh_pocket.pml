# PyMOL script: PCNA 1W60 (apo) with AOH1996 pocket highlighted
# Run: pymol -c scripts/pymol/pcna_1w60_aoh_pocket.pml
# Or:  pymol scripts/pymol/pcna_1w60_aoh_pocket.pml  (interactive)
#
# Pocket residue key:
#   RED    — known AOH1996-binding residues (from 8GLA GT set)
#   ORANGE — novel GNN-predicted pocket extensions
#   GRAY   — PCNA scaffold

import os, sys

# ── Output path ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
OUT_PNG    = os.path.join(REPO_ROOT, "reports", "figures", "pcna_aoh1996_pocket_highlight.png")
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)

# ── Fetch / load 1W60 ────────────────────────────────────────────────────────
raw_path = os.path.join(REPO_ROOT, "data", "raw", "1W60.pdb")
if os.path.exists(raw_path):
    cmd.load(raw_path, "pcna")
else:
    cmd.fetch("1W60", name="pcna", async_=0)

# Remove waters, ions, and non-polymer HETATM that are not the ligand of interest
cmd.remove("solvent")
cmd.remove("resn HOH+WAT+SO4+EDO+PEG+GOL+DMS+PO4+MPD+FMT+ACT+MES+BME+DTT")
cmd.remove("resn MG+CA+ZN+MN+FE+CU+NA+K")

# ── Residue selection strings ─────────────────────────────────────────────────
# GT-confirmed AOH1996 contact residues (union across chains A & B from 8GLA labels)
KNOWN_RESI = "25+26+27+38+39+40+41+42+44+45+46+47+123+125+126+128+231+232+233+234+250+251+252+253"
# GNN-predicted extensions not in GT set
NOVEL_RESI = "43+121+122+124+127+254+255"

cmd.select("pcna_all",  "pcna and polymer.protein")
cmd.select("known_aoh", f"pcna and polymer.protein and resi {KNOWN_RESI}")
cmd.select("novel_ext", f"pcna and polymer.protein and resi {NOVEL_RESI}")
cmd.select("scaffold",  "pcna_all and not known_aoh and not novel_ext")

# ── Representation ────────────────────────────────────────────────────────────
cmd.hide("everything", "all")
cmd.show("cartoon",    "pcna_all")
cmd.show("sticks",     "known_aoh")
cmd.show("sticks",     "novel_ext")

# ── Colors ────────────────────────────────────────────────────────────────────
# Scaffold: pale steel-blue (distinguishable from background without being loud)
cmd.color("0x9eb8d9", "scaffold")          # pale cornflower blue
cmd.color("0xdc3545", "known_aoh")         # confident red
cmd.color("0xff8c00", "novel_ext")         # amber-orange

# Refine stick coloring by element for residue detail
cmd.util.cnc("known_aoh")   # color-by-element but keep C atoms their selection color
cmd.util.cnc("novel_ext")
# Re-apply carbon colors after cnc resets them
cmd.color("0xdc3545", "known_aoh and elem C")
cmd.color("0xff8c00", "novel_ext and elem C")

# ── Transparent surface for pocket ───────────────────────────────────────────
cmd.select("pocket_region", f"pcna and polymer.protein and resi {KNOWN_RESI}+{NOVEL_RESI}")
cmd.create("pocket_surf", "pocket_region")
cmd.show("surface", "pocket_surf")
cmd.color("0xdc3545", "pocket_surf")
cmd.set("transparency", 0.55, "pocket_surf")
cmd.set("surface_quality", 1)

# ── Scene settings ────────────────────────────────────────────────────────────
cmd.bg_color("white")
cmd.set("ray_shadow",          0)
cmd.set("ray_opaque_background", 1)
cmd.set("antialias",           4)
cmd.set("depth_cue",           1)
cmd.set("fog_start",           0.45)
cmd.set("cartoon_fancy_helices", 1)
cmd.set("cartoon_smooth_loops",  1)
cmd.set("cartoon_highlight_color", "grey50")
cmd.set("spec_reflect",        0.4)
cmd.set("specular",            0.3)

# ── View: face-on to PCNA ring (ring axis along Z after orient) ───────────────
cmd.orient("pcna_all")
cmd.rotate("x", 90)
cmd.zoom("pcna_all", buffer=4)

# ── Labels ────────────────────────────────────────────────────────────────────
cmd.set("label_size",    18)
cmd.set("label_font_id", 7)
cmd.set("label_color",   "black")
# Label CA atoms of highlighted residues only
cmd.label("known_aoh and name CA", "resn+' '+resi")
cmd.label("novel_ext  and name CA", "resn+' '+resi")

# ── Render & save ─────────────────────────────────────────────────────────────
cmd.set("ray_trace_mode", 1)   # full ray trace
cmd.ray(3000, 3000)
cmd.png(OUT_PNG, dpi=300, ray=0)   # ray already done above
print(f"[DONE] Saved: {OUT_PNG}")
