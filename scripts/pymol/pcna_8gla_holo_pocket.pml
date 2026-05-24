# PyMOL script: PCNA 8GLA (holo, AOH1996-bound) — ligand + pocket view
# Run: pymol -c scripts/pymol/pcna_8gla_holo_pocket.pml
#
# Pocket residue key:
#   RED     — known AOH1996 contact residues (GT labels from aoh_gate_check.py)
#   ORANGE  — GNN-predicted pocket extensions
#   YELLOW  — AOH1996 ligand atoms
#   GRAY    — PCNA scaffold
#   SURFACE — pocket surface, semi-transparent red

import os, sys

# ── Output path ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.normpath(os.path.join(SCRIPT_DIR, "..", ".."))
OUT_PNG    = os.path.join(REPO_ROOT, "reports", "figures", "pcna_8gla_holo_pocket.png")
os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)

# ── Fetch / load 8GLA ────────────────────────────────────────────────────────
raw_path = os.path.join(REPO_ROOT, "data", "raw", "8GLA.pdb")
if os.path.exists(raw_path):
    cmd.load(raw_path, "pcna")
else:
    cmd.fetch("8GLA", name="pcna", async_=0)

# Clean non-essential small molecules; KEEP AOH1996 ligand
SOLVENT = "HOH+WAT+SO4+EDO+PEG+GOL+DMS+PO4+MPD+FMT+ACT+MES+BME+DTT"
IONS    = "MG+CA+ZN+MN+FE+CU+NA+K+CD"
cmd.remove("solvent")
cmd.remove(f"resn {SOLVENT}")
cmd.remove(f"resn {IONS}")

# ── Identify AOH1996 ligand ───────────────────────────────────────────────────
# AOH1996 is typically coded as "AOH" or "AH9" in the RCSB entry; check both.
# If neither resolves, fall back to any remaining HETATM.
cmd.select("lig_aoh", "resn AOH or resn AH9 or resn AOH1")
lig_count = cmd.count_atoms("lig_aoh")
if lig_count == 0:
    # Try any remaining HETATM not polymer
    cmd.select("lig_aoh", "hetatm and not polymer")
    lig_count = cmd.count_atoms("lig_aoh")
    if lig_count == 0:
        print("[WARN] AOH1996 ligand not found — rendering protein only")

# ── Residue selection strings ─────────────────────────────────────────────────
# GT set uses both chain A and B from aoh_gate_check.py
KNOWN_RESI = "25+26+27+38+39+40+41+42+44+45+46+47+123+125+126+128+231+232+233+234+250+251+252+253"
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

if lig_count > 0:
    cmd.show("sticks",    "lig_aoh")
    cmd.show("spheres",   "lig_aoh")          # spheres to make ligand pop
    cmd.set("sphere_scale", 0.35, "lig_aoh")

# ── Colors ────────────────────────────────────────────────────────────────────
cmd.color("0x9eb8d9", "scaffold")
cmd.color("0xdc3545", "known_aoh")
cmd.color("0xff8c00", "novel_ext")

if lig_count > 0:
    cmd.util.cbay("lig_aoh")     # color-by-element with yellow carbons
    # Override carbon color to a warm gold to distinguish from extensions
    cmd.color("0xf0d060", "lig_aoh and elem C")

# Apply element-based coloring for heteroatoms in pocket residues
cmd.util.cnc("known_aoh")
cmd.util.cnc("novel_ext")
cmd.color("0xdc3545", "known_aoh and elem C")
cmd.color("0xff8c00", "novel_ext and elem C")

# ── Transparent surface: whole PCNA ring (shows channel + pocket) ─────────────
cmd.create("ring_surf", "pcna_all")
cmd.show("surface", "ring_surf")
cmd.color("0x9eb8d9", "ring_surf")
cmd.set("transparency", 0.72, "ring_surf")
cmd.set("surface_quality", 1)

# ── Focused pocket surface ────────────────────────────────────────────────────
cmd.select("pocket_region", f"pcna and polymer.protein and resi {KNOWN_RESI}+{NOVEL_RESI}")
cmd.create("pocket_surf", "pocket_region")
cmd.show("surface", "pocket_surf")
cmd.color("0xdc3545", "pocket_surf")
cmd.set("transparency", 0.45, "pocket_surf")

# ── Scene settings ────────────────────────────────────────────────────────────
cmd.bg_color("white")
cmd.set("ray_shadow",            0)
cmd.set("ray_opaque_background", 1)
cmd.set("antialias",             4)
cmd.set("depth_cue",             1)
cmd.set("fog_start",             0.40)
cmd.set("cartoon_fancy_helices", 1)
cmd.set("cartoon_smooth_loops",  1)
cmd.set("cartoon_highlight_color", "grey50")
cmd.set("spec_reflect",          0.4)
cmd.set("specular",              0.3)

# ── View: orient on ligand region if found, else ring face ───────────────────
if lig_count > 0:
    # Center on the ligand–pocket interface, then pull back
    cmd.orient("pocket_region")
    cmd.zoom("pocket_region", buffer=8)
    cmd.rotate("x", 15)   # slight tilt to show depth
    cmd.rotate("y", -20)
else:
    cmd.orient("pcna_all")
    cmd.rotate("x", 90)
    cmd.zoom("pcna_all", buffer=4)

# ── Labels ────────────────────────────────────────────────────────────────────
cmd.set("label_size",    18)
cmd.set("label_font_id", 7)
cmd.set("label_color",   "black")
cmd.label("known_aoh and name CA", "resn+' '+resi")
cmd.label("novel_ext  and name CA", "resn+' '+resi")

# ── Render & save ─────────────────────────────────────────────────────────────
cmd.set("ray_trace_mode", 1)
cmd.ray(3000, 3000)
cmd.png(OUT_PNG, dpi=300, ray=0)
print(f"[DONE] Saved: {OUT_PNG}")
