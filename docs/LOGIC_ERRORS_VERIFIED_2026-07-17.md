# GNN‑PCNA — Verified Code Logic Errors

*Generated 2026‑07‑17. Independent re‑verification of the 63‑item bug ledger from the latest push (branch `graph-leakage-fix`, tip `b12c0d4`, GNN‑PCNA research repo).*

## What this document is

You asked for the errors found in the GNN framework on the latest push, filtered down to **actual code logic errors** — not scientific assumptions borrowed from the literature. So every one of the 63 findings in the prior ledger (`docs/BUG_LEDGER_2026-07-17.md`) was re‑checked against the **real audited source** (recovered from git history where the files were later rewritten), by two independent agents per finding: one classifier and one adversarial verifier told to demote anything that only looks wrong through a domain/statistics lens.

**A finding is kept as a code logic error only if a competent engineer would call it a bug from the code alone** — a self‑contradiction with the code's own docstring/comment/intent, a deterministic wrong/crashing/degenerate result, a dead or unreachable branch — with *no appeal to molecular‑dynamics or ML literature required*. Findings whose "wrongness" needs a scientific judgment (better observable, better cutoff, standard MD practice, statistical independence) are pulled out into a separate section so you can see exactly which ones they are.

## Result

| Outcome | Count |
|---|---|
| **Actual code logic errors** (kept) | **41** |
| Literature / methodology assumptions (reclassified out) | 22 |
| Not reproducible in the code | 0 |
| **Total ledger findings re‑checked** | **63** |

So of the ~62–63 findings on that push, **41 are genuine logic errors in the code**; the remaining 22 are real-but-debatable *scientific* critiques (a convex hull is the wrong cavity observable, an ANM cutoff should follow Atilgan 2001, MD needs PBC unwrapping, Cohen's d should use replicate‑level n, …). Those 22 are listed in Part 2 with the specific reason each is a methodology call rather than a code bug — that is the "assumptions from literature" you wanted separated out.

**Severity of the 41 logic errors:** 🔴 critical 2 · 🟠 high 9 · 🟡 medium 11 · ⚪ low 19

---

## Part 1 — Actual code logic errors (41)

Each entry: severity, the offending code (from the audited source), what the code does wrong, and why it is a code‑provable bug and not a literature assumption. Ledger IDs are preserved for cross‑reference.

### `scripts/run_md_analysis.py`
<sub>audited pre-fix source @ `d7cf76d`</sub>

#### 🔴 CRITICAL — BUG‑1: AlignTraj(in_memory=False) does not rewire u; RMSF on unaligned coordinates

```python
52	    # in_memory=False streams to a temp file (safe for large DCD); run() with no step aligns
53	    # all frames so RMSF.run(step=stride) below doesn't double-skip frames
54	    align.AlignTraj(u, ref, select="backbone", in_memory=False).run()
...
59	    rmsf_calc = rms.RMSF(ca).run(step=stride)
```
- **The bug:** compute_rmsf's docstring (line 42, 'Align trajectory to first frame on backbone, then compute Ca RMSF') and inline comment assert the trajectory is aligned before RMSF, but align.AlignTraj(...) is called with in_memory=False, which (documented MDAnalysis API behavior) writes aligned frames to a separate on-disk file and does NOT replace u.trajectory. Line 59's rms.RMSF(ca).run() re-iterates the original, still-unaligned u, so the function fails to do what its own docstring says.
- **How it fails:** AlignTraj(in_memory=False) returns without rewiring u; after run() the reader rewinds and RMSF re-reads original coordinates from disk, so per-residue RMSF retains whole-molecule rigid-body translation/rotation. Fix = in_memory=True (or reload the written file). Provable from MDAnalysis API docs + the docstring, no scientific literature required.
- **Why it counts as a logic error (not literature):** Self-contained code-intent-vs-behavior contradiction: the function CALLS align (declaring intent) but the call is a no-op on the measured universe per the API. A competent engineer sees the bug from docstring + API alone. The 'circular alignment' hazard is moot precisely because alignment never takes effect, which confirms the defect is reproducible, not a phantom.
- *Separated methodology overlay (not part of the bug):* The downstream framing that the resulting RMSF is 'scientifically invalid', that pocket-vs-background fold-change is meaningless, and the advice to align on a stable non-pocket core (anti-circularity) are domain overlays not needed to see the code-intent contradiction.

#### 🟠 HIGH — BUG‑2: Pocket-volume hull built from residues across all chains (chain-agnostic mask)

```python
114	        mask = np.array([r in pocket_resids for r in resids])
...
220	    vol_result = compute_pocket_volume(u, AOH_GT, stride=args.stride)
```
- **The bug:** compute_pocket_volume masks Ca atoms by residue NUMBER only (line 114), and line 220 passes AOH_GT, the union that collapses AOH_GT_BY_CHAIN. The code's own dict shows the same numbers exist in chains A and B (e.g. 25 in both, lines 33/35), so matching r in AOH_GT selects that residue in every chain; the ConvexHull is built over a Ca cloud spanning multiple subunits, not one pocket. Chain-distinguishing data (AOH_GT_BY_CHAIN, ca.segids) is available and discarded.
- **How it fails:** chains/segids are never consulted at line 114; the union at line 38 is passed at line 220, so pocket_coords aggregates Ca atoms from all chains carrying those numbers. Provable directly from the code's own per-chain dict (which documents the residue-number collision across chains) and the presence of an unused chain-aware structure.
- **Why it counts as a logic error (not literature):** The code discards chain information it itself maintains (AOH_GT_BY_CHAIN keyed A/B, with overlapping numbers), and matches a single number across every chain — a code-provable information-loss defect, independent of any literature about cavities.
- *Separated methodology overlay (not part of the bug):* The claims that the hull therefore measures the whole ring/dimer, is 'flat by construction', overestimates, and that a Ca convex hull is the wrong observable (use fpocket/MDpocket or interface SASA) are geometry/domain judgments layered on top.

#### 🟠 HIGH — BUG‑3: RMSF pocket mask chain-agnostic; chain data captured but unused for masking

```python
38	AOH_GT = set().union(*AOH_GT_BY_CHAIN.values())
...
168	    resids, chains, rmsf = compute_rmsf(u, stride=args.stride)
...
170	    pocket_mask = np.array([r in AOH_GT for r in resids])
...
190	            {"resid": int(resids[i]), "chain": str(chains[i]),
```
- **The bug:** chains is captured from compute_rmsf at line 168 but referenced only for JSON output at line 190; the pocket_mask at line 170 matches residue NUMBER against AOH_GT (union) with no chain filter. So every residue with a matching number in every chain is flagged, and single-chain-only residues (e.g. 23, present only in B's set, line 35) are flagged in the other chain too. The chain data needed to fix it is captured and thrown away.
- **How it fails:** pocket_mask never indexes chains[i]; pocket_rmsf/bg_rmsf, aoh_pocket_residues (line 247), and the pocket DCCM subset are all computed over a chain-mixed residue set. Minor ledger nuance confirmed: AOH_GT_BY_CHAIN is used at line 38 to build the union, so it is not entirely unused — but it is never used for chain-aware matching.
- **Why it counts as a logic error (not literature):** Captured-but-unused chain variable plus a mask that provably matches across chains is a code-level defect, not a scientific opinion; the magnitude claim is the only part needing domain input, and I separated it.
- *Separated methodology overlay (not part of the bug):* The specific magnitude ('~3x inflation', chain-C contamination) is input/structure-dependent, and the biological claim that the AOH pocket exists only at the A-B interface is a domain overlay. The segids-vs-chainIDs implementation caveat is also domain-specific.

#### ⚪ LOW — BUG‑6: Formatted prints crash on None RMSF/fold_change; truthiness guard mishandles 0.0

```python
171	    pocket_rmsf = float(rmsf[pocket_mask].mean()) if pocket_mask.any() else None
...
173	    fold_change = round(pocket_rmsf / bg_rmsf, 3) if pocket_rmsf and bg_rmsf else None
...
175	    print(f"  Pocket RMSF : {pocket_rmsf:.3f} Å")
176	    print(f"  Background  : {bg_rmsf:.3f} Å")
177	    print(f"  Fold-change : {fold_change:.3f}")
```
- **The bug:** pocket_rmsf, bg_rmsf and fold_change can each be None (lines 171-173), and lines 175-177 apply ':.3f' to them unconditionally; f"{None:.3f}" raises TypeError, aborting the run before any file is written. Separately, fold_change's guard uses truthiness ('if pocket_rmsf and bg_rmsf', line 173), so a legitimate 0.0 would be mis-treated as None. (Line 215 has the same unguarded ':.4f' on a possibly-None pocket_dccm.)
- **How it fails:** An all-False pocket_mask (e.g. after adopting chain-aware matching with a segid/chainID mismatch that selects nothing) sets pocket_rmsf=None; line 175 then raises TypeError with no output written. The rubric explicitly lists 'format-string on a value that can be None -> TypeError crash' as a code logic error. Line 270 is guarded (f-string only evaluated when truthy) so it does not crash, though its truthiness guard misprints a genuine 0.0.
- **Why it counts as a logic error (not literature):** Code condition exists and is reproducible on the None branch the code itself creates; matches the rubric's format-on-None example. Agree.
- *Separated methodology overlay (not part of the bug):* None — pure control-flow/typing defect. The only non-code caveat is that under current 1W60 inputs pocket_mask.any() is True so None does not arise, making it a latent crash rather than an active one; that is a triggering condition, not a domain judgment.

#### ⚪ LOW — BUG‑7: Dead variable vols_clean computed but never used

```python
224	        vols_clean = [v for v in volumes if not (isinstance(v, float) and v != v)]
225	        mean_vol = float(np.nanmean(volumes))
226	        max_vol  = float(np.nanmax(volumes))
```
- **The bug:** vols_clean (line 224, a NaN-filtered copy) is never referenced again; grep confirms it appears only at line 224. mean_vol/max_vol at lines 225-226 use np.nanmean/np.nanmax on the raw volumes instead, so the NaN-filtering intent is computed and discarded.
- **How it fails:** The list comprehension runs and its result is dropped; statistics are taken from volumes. Purely a dead/unused-variable defect provable from the source, matching the rubric's 'dead/unused variable' example. No functional impact on outputs.
- **Why it counts as a logic error (not literature):** Verified by grep: vols_clean occurs once. Dead code is an explicit rubric CODE_LOGIC_ERROR category. Agree.
- *Separated methodology overlay (not part of the bug):* None. The adjacent note that np.nanmean over an all-NaN list emits a RuntimeWarning and returns NaN is a robustness observation, not a domain judgment.


### `src/md/parse_trajectory.py`
<sub>audited pre-fix source @ `d7cf76d`</sub>

#### 🔴 CRITICAL — BUG‑8: track_pocket_volume selects pocket residues across all chains

```python
82:    resid_sel = ' or '.join(f'resid {r}' for r in pocket_residue_ids)
83:    pocket_ca = u.select_atoms(f'({resid_sel}) and name CA')
```
- **The bug:** The selection is assembled from bare `resid N` tokens with no segid/chain qualifier. In MDAnalysis the `resid` keyword matches by residue number across every segment of the Universe, so on any multi-chain topology whose subunits reuse the same numbering, `pocket_ca` collects that residue in EVERY chain. That contradicts the code's own intent (variable named `pocket_ca`, docstring 'convex hull of Ca coords' to estimate a single pocket's volume): the atom set is over-selected relative to the one intended pocket. This is provable from MDAnalysis selection semantics alone, no appeal to literature.
- **How it fails:** pocket_residue_ids=[50,120,...] -> resid_sel='resid 50 or resid 120 or ...' -> select_atoms('(...) and name CA') returns the 50/120/... Ca in chain A AND B AND C. ConvexHull over that multi-subunit point cloud measures the trimer envelope rather than the intended cavity, so the per-frame trace is nearly flat -> the reported 'pocket has no dynamics'.
- **Why it counts as a logic error (not literature):** I agree with stage 1. The offending line lacks a chain qualifier and MDAnalysis `resid` is segment-unscoped; a competent engineer flags this as an over-broad selection from the code + library semantics alone. This matches the prompt's canonical 'residue matching ignores chain -> selects all 3 chains' code-error example. Conditional on multi-chain input, but the correctness defect (missing segid scoping vs. single-pocket intent) is a code/library fact, not a quantitative domain estimate.
- *Separated methodology overlay (not part of the bug):* That a Ca convex hull is a poor observable for a cryptic cavity (SASA / inter-chain opening distance / per-frame fpocket-MDpocket would be better) and that PBC unwrap should precede the measurement are domain/methodology critiques layered on top of the selection bug.

#### 🟠 HIGH — BUG‑9: Homotrimer resid collision -> dict last-write-wins maps every pocket residue to one subunit

```python
33:    return ca_atoms.resids.copy(), rmsf_calc.rmsf.copy()
119:    # Map PDB resid -> array index so we index rmsf_values correctly
120:    resid_to_idx = {int(rid): i for i, rid in enumerate(residue_ids)}
121:    pocket_arr_idx = np.array([
122:        resid_to_idx[r] for r in pocket_residue_ids if int(r) in resid_to_idx
123:    ])
```
- **The bug:** resid_to_idx is a dict comprehension keyed on the bare integer resid over residue_ids, and residue_ids is `ca_atoms.resids` (line 33) which contains each residue number once per chain in a multimer. Duplicate keys overwrite, so only the last occurrence's index survives; the map is not one-to-one. The line-119 comment states the intent is to index rmsf_values 'correctly', yet for any repeated resid the code silently collapses all copies to one arbitrary (last-in-atom-order) index. This is a pure Python dict last-write-wins fact plus the code's own stated intent.
- **How it fails:** residue_ids=[1..L,1..L,1..L]; `{int(rid): i ...}` writes key 1 at i=0, again at i=L, again at i=2L; last write wins -> resid_to_idx[r] points into the final block. pocket_arr_idx then indexes rmsf_values/dccm at those rows, so mean_rmsf, mean_internal_dccm and rmsf_ratio are all computed on one arbitrary subunit's residues rather than the intended interface copies.
- **Why it counts as a logic error (not literature):** I agree with stage 1. This is the prompt's textbook 'dict keyed on a value that collides so last write wins and resolves to the wrong element'. Provable from Python semantics + the line-119 'correctly' comment; the identity of the surviving chain is the only part needing domain knowledge, and it is correctly isolated to methodology.
- *Separated methodology overlay (not part of the bug):* That the surviving copy is specifically chain C, and that chain C carries no pocket so RMSF/DCCM come out rigid, is PCNA domain context; it depends on atom ordering and biology but does not change the collision fact.

#### 🟠 HIGH — BUG‑11: Internal DCCM uses abs() -> drops sign

```python
44:        dccm : (N, N) float array, values in [-1, 1]
45:               C_ij = <dr_i.dr_j> / sqrt(<|dr_i|^2><|dr_j|^2>)
141:        mean_internal_dccm = float(np.abs(off_diag).mean())
```
- **The bug:** The module's own compute_dccm docstring (lines 44-45) formally defines DCCM as a SIGNED quantity in [-1,1], and compute_dccm returns clipped signed values that can be negative. summarize_md_validation then labels its result `mean_internal_dccm` but computes `np.abs(off_diag).mean()` -- the mean of magnitudes, not the mean of the (signed) DCCM. The name/return-value semantics contradict the module's own definition of DCCM: 'mean internal dccm' should be the mean of signed dccm entries, yet the sign is silently discarded. Provable from the code's own definitions.
- **How it fails:** off_diag containing {+0.9,-0.9} averages to 0.0 signed but np.abs(...).mean()=0.9, so anti-correlated pairs are mapped to +1; the value labeled mean_internal_dccm is biased upward toward 1 regardless of true concertedness.
- **Why it counts as a logic error (not literature):** I agree with stage 1. This is the prompt's exact 'abs() applied where the function's own purpose / sibling code requires the sign' example. The contradiction is internal: compute_dccm defines and returns signed values, summarize abs()-es them under a name that reads as mean DCCM. No literature needed to see the label/definition mismatch; the physical significance of sign is the separable methodology overlay.
- *Separated methodology overlay (not part of the bug):* The physical rationale -- that sign distinguishes concerted (correlated) opening from hinge/anti-correlated interface motion, and that run_nma.py reports the signed mean -- is the domain justification for why the signed mean is the right observable.


### `scripts/make_md_figures.py`
<sub>audited pre-fix source @ `d7cf76d`</sub>

#### 🟡 MEDIUM — BUG‑16: DCCM pocket box drawn as one min-to-max block over scattered pocket indices

```python
155:     poc_idx    = np.where(in_aoh)[0]
158:     if len(poc_idx) >= 2:
159:         sub = dccm[np.ix_(poc_idx, poc_idx)]
174:         lo, hi = poc_idx.min() - 0.5, poc_idx.max() + 0.5
175:         rect   = mpatches.Rectangle((lo, lo), hi-lo, hi-lo,
177:                                      facecolor="none", label="AOH1996 pocket")
```
- **The bug:** Within the SAME function the reported metric selects poc_idx as a scattered index set — dccm[np.ix_(poc_idx, poc_idx)] with np.triu_indices (line 159-160) — while the annotation draws a single contiguous min→max square (lines 174-175) labeled 'AOH1996 pocket' (line 177). np.ix_ and a min..max slice are equivalent ONLY if poc_idx is contiguous; the code's use of np.ix_ shows the design anticipates a non-contiguous pocket, so the box and the metric describe different residue sets and the box label overclaims. The in-file AOH_GT (lines 33-34) independently documents the author's pocket model as scattered residue numbers {25,26,27,38,…,253}.
- **How it fails:** For a scattered poc_idx (e.g. positions 10,11,12,50,51) the metric averages correlations only among those 5 residues, but the drawn rectangle spans 10→51 — a 42×42 block dominated by non-pocket residues — while the legend calls the block the pocket. The mismatch is a self-contained code inconsistency (np.ix_ scattered selection vs. min..max box) corroborated by the in-file scattered AOH_GT.
- **Why it counts as a logic error (not literature):** Kept as CODE_LOGIC_ERROR: unlike 15, there is an internal inconsistency provable within the file — the same variable poc_idx is treated as scattered by the reported metric (np.ix_) yet as a contiguous block by the annotation, and the in-file AOH_GT documents the pocket as non-consecutive residues. A pure code reviewer sees the box overclaims whenever poc_idx is non-contiguous, which the code's own scatter-aware metric presupposes. The best-alternative encoding is the only methodology overlay.
- *Separated methodology overlay (not part of the bug):* The choice among alternative encodings (per-segment rectangles, tick/scatter overlay of the exact indices, per-chain-pair sub-blocks) is a visualization-design preference, not a code defect.

#### 🟡 MEDIUM — BUG‑17: Rolling mean zero-fills NaN frames and uses mode='same' → downward bias + edge ramp

```python
121:     win = max(1, len(vols) // 10)
122:     roll = np.convolve(np.where(np.isnan(vols), 0, vols),
123:                        np.ones(win)/win, mode="same")
```
- **The bug:** Two deterministic numerical defects, both provable without any domain appeal. (1) NaN frames are replaced by 0 (np.where(np.isnan(vols),0,vols)) then convolved with a kernel normalized by the full window (np.ones(win)/win); any window overlapping a missing frame sums a spurious 0 yet still divides by win, biasing the 'rolling mean' toward zero. A correct rolling mean of data-with-gaps divides by the count of valid samples (conv(filled)/conv(mask)). (2) mode='same' with a normalized box kernel implicitly zero-pads the ends, so the first/last ~win/2 outputs sum fewer real samples while still dividing by win, producing an artificial ramp toward zero at both trajectory ends.
- **How it fails:** Defect (2) is unconditional — a box-kernel 'same' convolution always ramps at the edges regardless of data. Defect (1) requires NaNs to exist, but the code's own np.isnan guard is direct in-file evidence the author expects NaN frames; given they occur, missing frames are treated as 0 Å³ pockets, manufacturing spurious dips. The label 'Rolling mean' (line 127) states the intent, and the behavior is not the mean of the valid data — an intent/behavior mismatch.
- **Why it counts as a logic error (not literature):** CODE_LOGIC_ERROR stands: the edge-ramp artifact is unconditional code behavior, and the zero-fill bias is a textbook falsy/missing-handling numerical bug whose expectation of NaNs is documented by the code's own np.isnan guard. No literature is needed to see 'Rolling mean' does not compute the mean of the valid samples.
- *Separated methodology overlay (not part of the bug):* The separate claim that a Cα convex hull cannot measure pocket breathing at all is a distinct scientific critique (belongs to finding 18), not part of this numerical defect.

#### ⚪ LOW — BUG‑19: Truthiness tests conflate 0.0 with missing for fold-change and pocket-mean

```python
64:     fc_md    = data.get("fold_change_pocket_vs_bg") or \
90:     if mean_poc:
94:     fc_str = f"{fc_md:.3f}" if fc_md else "n/a"
```
- **The bug:** Three classic falsy-vs-None conflations, provable without domain input. Line 64: `data.get(...) or (recompute)` discards a legitimately stored 0.0 and recomputes. Line 94: `f"{fc_md:.3f}" if fc_md else "n/a"` prints 'n/a' when fc_md is exactly 0.0 instead of '0.000'. Line 90: `if mean_poc:` suppresses the pocket-mean line when the pocket RMSF mean is 0.0 (note mean_poc is already None-guarded at line 88, so the None case is handled — only the 0.0 case is the bug). All should use `is not None`.
- **How it fails:** For any 0.0-valued input the code treats the value as absent: caption shows 'MD=n/a' rather than '0.000', or the pocket-mean axhline silently vanishes. Deterministic given a 0.0 value.
- **Why it counts as a logic error (not literature):** CODE_LOGIC_ERROR stands: conflating 0.0 with missing is a self-evident Python truthiness bug independent of whether 0.0 actually occurs — the prompt lists falsy-float / None-format bugs as canonical code logic errors. The 'does 0.0 ever happen' concern is only an impact overlay.
- *Separated methodology overlay (not part of the bug):* Whether a 0.0 fold-change or 0.0 pocket-mean ever arises in a real MD trajectory is an empirical/domain judgment about input plausibility; it affects impact, not the existence of the defect.

#### ⚪ LOW — BUG‑20: AOH_GT ground-truth set defined but never used; figure trusts JSON flag with no chain check

```python
33: AOH_GT = {25,26,27,38,39,40,41,42,44,45,46,47,
34:           123,125,126,128,231,232,233,234,250,251,252,253}
61:     in_aoh   = np.array([r["in_aoh_pocket"] for r in residues])
154:     in_aoh     = np.array([r["in_aoh_pocket"] for r in residues])
```
- **The bug:** AOH_GT is defined at module scope (lines 33-34) and never referenced anywhere else — I grepped the file and 'AOH_GT' appears on exactly one line (33). It is confirmed dead code: pocket membership everywhere comes from the JSON field r['in_aoh_pocket'] (lines 61, 154); only IDCL, not AOH_GT, is actually consumed (line 81). An unused module-scope variable is a self-evident code defect.
- **How it fails:** AOH_GT is computed then never read; deleting it changes no output — the definition of dead code. The chain-C contamination risk cannot be seen from this file since in_aoh_pocket is supplied externally.
- **Why it counts as a logic error (not literature):** CODE_LOGIC_ERROR stands on the dead-code core (grep-confirmed single occurrence): 'dead/unused variable' is explicitly a code logic error. The chain-cross-check half is a domain overlay and is correctly split out; it does not upgrade or block the dead-code verdict.
- *Separated methodology overlay (not part of the bug):* The second half — that trusting the residue-number-only in_aoh_pocket flag risks including chain-C residues and that the figure should cross-check chain-aware (A/B-only) membership — is a data-provenance/domain concern requiring knowledge that the AOH pocket is chain-specific; it is not observable from this file because the JSON is external.


### `src/data_processing/graph_construction.py`
<sub>audited pre-fix source @ `20ba9a7`</sub>

#### 🟠 HIGH — BUG‑22: Backbone edges and is_backbone built from array-index separation, not resid — false peptide bonds across numbering gaps

```python
256:    raw_sep   = np.abs(i_idx - j_idx).astype(np.float32)
260:    is_backbone = (same_chain.astype(bool) & (raw_sep == 1)).astype(np.float32)
287:    idx_sep    = np.abs(arr_idx[:, None] - arr_idx[None, :])           # (N, N)
288:    mask = same_chain & (idx_sep >= 1) & (idx_sep <= max_sep)
250:    Sequential separation uses array-index distance (not PDB resid numbers)
251:    so PDB numbering gaps do not produce wrong seq_sep or is_backbone values.
325:    raw_sep    = np.abs(resids[i_idx] - resids[j_idx]).astype(np.float32)
```
- **The bug:** is_backbone and the backbone edge mask are derived from array-index separation with only a same-chain guard; true sequence adjacency (resids diff==1) is never checked. The docstrings at 250-252 and 279-282 assert that using array indices AVOIDS numbering-gap problems — this is the logical inverse of reality: array-adjacency is precisely what bridges a numbering gap into a false peptide bond. In-file proof that array index != resid: the file stores a separate resids array (line 366) and the v1 sibling computes the identical seq_sep feature from resids (line 325). So the intended resid-based semantics and the array/resid divergence are both established within this file.
- **How it fails:** For an internal intra-chain gap (e.g. resid 118 followed by resid 133 after a disordered loop), those two array-adjacent Residue objects satisfy same_chain and idx_sep==1, so the code emits a backbone edge with is_backbone=1 and seq_sep ~1/20 — asserting a peptide bond that does not exist. The inverted docstring claim is unconditionally false; the numeric false-bond manifests whenever an internal gap exists.
- **Why it counts as a logic error (not literature):** A competent engineer comparing line 256/260 to the v1 resid-based line 325 sees the same-feature divergence, and reads a docstring whose justification is the exact opposite of what the code does. Both are provable from this file with no appeal to literature. CODE_LOGIC_ERROR stands.
- *Separated methodology overlay (not part of the bug):* Only the 'flexible loops are the regions of interest for cryptic-pocket dynamics' framing is a domain overlay used to argue severity; it is not needed to see the docstring is inverted or that v1 and v2 disagree.

#### 🟡 MEDIUM — BUG‑23: Pseudo-dihedrals computed over array-adjacent Ca that may span a numbering gap

```python
105:    """Cα pseudo-dihedral angle in radians between 4 consecutive Cα atoms."""
140:        if (1 <= i < N - 2
141:                and chain_ids[i-1] == chain_ids[i] == chain_ids[i+1] == chain_ids[i+2]):
142:            phi_arr[i] = _pseudo_dihedral(
143:                coords[i-1], coords[i], coords[i+1], coords[i+2])
```
- **The bug:** The phi/psi branches are gated only on chain-ID equality of array-adjacent residues; resid contiguity is never verified. The helper docstring (line 105) states the torsion is 'between 4 consecutive Cα atoms', and the same-chain guard itself demonstrates intent to compute only over genuinely-adjacent residues. In-file evidence that array-adjacent != sequence-consecutive: the separate resids array plus v1's resid usage at line 325. When an intra-chain gap exists, the four Cα passed are not consecutive, violating the function's own stated 'consecutive' contract.
- **How it fails:** For same-chain array-adjacent residues across a numbering gap (e.g. resid 118 then 133), coords[i-1..i+2] are handed to _pseudo_dihedral, producing sin/cos torsion values (node dims 30-33) over four Cα that are not the consecutive (i-1,i,i+1,i+2) residues the feature is defined as. The value is affirmatively wrong rather than the documented 0.0; manifests only when an internal gap exists.
- **Why it counts as a logic error (not literature):** Weaker than bug 22 (no false docstring claim, no resid-using sibling for this exact feature), but the 'consecutive' contract word, the same-chain guard revealing adjacency intent, and the in-file resids array/line 325 make it code-provable that array-adjacency can violate the stated contract. Same root cause as bug 22. Kept CODE_LOGIC_ERROR, confidence lowered to medium.
- *Separated methodology overlay (not part of the bug):* The 'fabricates backbone geometry at loop boundaries relevant to pocket breathing' / physical-meaninglessness characterization is a domain overlay used to judge severity; the code-provable core is the docstring 'consecutive' contract vs a guard that checks chain but not resid contiguity.

#### ⚪ LOW — BUG‑25: v2 contact-graph seq_sep uses array-index separation while v1 uses resid — inconsistent feature semantics

```python
256:    raw_sep   = np.abs(i_idx - j_idx).astype(np.float32)
325:    raw_sep    = np.abs(resids[i_idx] - resids[j_idx]).astype(np.float32)
```
- **The bug:** _build_edge_attr (used for the v2 contact graph via line 379) computes seq_sep from array-index separation (line 256), whereas the v1 public builder computes the same documented edge feature (layout line 35: 'seq_sep_norm — |i-j|/20') from resid separation (line 325). The two public APIs emit inconsistent semantics for the identical documented feature slot. The inconsistency is provable purely by comparing line 256 to line 325; no domain judgment is needed for the divergence itself.
- **How it fails:** For two same-chain residues 15 apart in resid numbering but array-adjacent across a gap, v1 emits seq_sep = min(15,20)/20 = 0.75 while v2 emits min(1,20)/20 = 0.05 for the same contact edge; checkpoints trained under one convention silently mismatch the other. The numeric divergence needs an internal gap; the semantic inconsistency between builders is always present.
- **Why it counts as a logic error (not literature):** An identically-documented feature computed two different ways across two public builders is an internal inconsistency a competent engineer flags from the code alone, independent of which convention is 'right'. CODE_LOGIC_ERROR (low severity) stands.
- *Separated methodology overlay (not part of the bug):* The 'understating seq_sep mislabels long-range contacts as near-neighbor, matters for local-vs-long-range reasoning' framing is a mild domain overlay for impact; the v1/v2 semantic divergence is unconditional and code-provable.

#### ⚪ LOW — BUG‑26: Chain one-hot (unique_chains[:3]) and chain_id_int (uncapped) derive from divergent mappings

```python
191:    unique_chains = sorted(set(chain_ids))
192:    chain_to_idx  = {c: k for k, c in enumerate(unique_chains[:3])}
215:        cidx = chain_to_idx.get(res.chain, -1)
389:    unique_chains = sorted(set(chain_ids))
390:    chain_to_int  = {c: k for k, c in enumerate(unique_chains)}
```
- **The bug:** The node-feature chain one-hot is built from sorted(set(chain_ids))[:3] (line 192, capped) with a 4th chain resolving to cidx=-1 → all-zero one-hot, while data.chain_id integer encoding uses sorted(set(chain_ids)) with no cap (line 390), giving a 4th chain chain_id_int=3. For any structure with >3 chains the two encodings on the same Data object deterministically disagree. Provable purely by comparing the two mappings; no domain judgment.
- **How it fails:** Feed a >3-chain structure: the 4th sorted chain's residues get an all-zero chain_onehot (cidx=-1) yet chain_id_int=3, so the one-hot and the integer chain encoding on the same object contradict each other; any downstream code reading data.chain_id vs the one-hot gets mismatched subunit identity. Latent for the current 3-chain homotrimer inputs.
- **Why it counts as a logic error (not literature):** Two divergent chain mappings (one capped, one not) on the same object are a code-provable inconsistency, matching the ledger's 'latent robustness defect' class. No literature needed. CODE_LOGIC_ERROR (low severity, currently latent) stands.
- *Separated methodology overlay (not part of the bug):* None material — pure code-consistency/robustness defect. The only non-code element is the empirical note that current PCNA inputs (1W60/8GLA/1AXC) have exactly 3 chains, so the divergence is latent today.


### `scripts/run_nma.py`
<sub>audited pre-fix source @ `d7cf76d`</sub>

#### 🟠 HIGH — BUG‑27: main() crashes with 'unsupported format string passed to NoneType' when a pocket metric is None

```python
255:    print(f"  Pocket RMSF (norm)        : {a['pocket_mean_rmsf_norm']:.4f}")
214:            "pocket_mean_rmsf_norm": round(pocket_rmsf, 4) if pocket_rmsf else None,
175:    pocket_rmsf  = float(rmsf_norm[aoh_mask].mean())  if aoh_mask.any() else None
```
- **The bug:** The code itself assigns None to pocket_rmsf/bg_rmsf/fold_change (lines 175-177) and to pocket_internal_corr (line 186), which flow into the JSON as None at lines 214-216 and 226. main() then formats those same dict values with :.4f/:.3f at lines 255-258. format(None, '.4f') raises TypeError deterministically. Note the f-string at line 219 is safe because it lives in the branch selected only when fold_change>1.0, but the four bare prints at 255-258 have no such guard.
- **How it fails:** Input with no AOH residue match -> aoh_mask all False -> pocket_rmsf=None (175) -> JSON null (214) -> line 255 evaluates {None:.4f} -> TypeError. The JSON was already written at line 238, so it is a hard failure at the final print, not silent data loss.
- **Why it counts as a logic error (not literature):** A format spec on a value the code itself can set to None is a self-evident crash provable from the code with zero appeal to literature. Verdict stands.
- *Separated methodology overlay (not part of the bug):* WHICH realistic inputs drive aoh_mask.any() to False (lowercase/blank chains, chain-C-only, residue-numbering offset) is PDB-domain reasoning, but it is not needed to prove the crash — any None reaching lines 255-258 crashes regardless of why.

#### 🟡 MEDIUM — BUG‑28: Interpretation strings assert a biological conclusion from marginal fold-change / any positive DCCM (plus comment vs code abs() mismatch)

```python
179:    # Pocket DCCM: mean absolute internal correlation among AOH residues
184:        pocket_internal_corr = float(off_diag.mean())
230:            ) if pocket_internal_corr and pocket_internal_corr > 0 else None,
```
- **The bug:** Comment/code mismatch: line 179 documents 'mean ABSOLUTE internal correlation' but line 184 computes the signed mean off_diag.mean() with no abs(). The two diverge whenever any off-diagonal DCCM entry is negative, and the signed value is then fed to a signed '> 0' gate at line 230 (which abs() would render near-vacuous). This is a doc-vs-code contradiction analogous to 'docstring says sorted but code never sorts' — provable from the code's own comment, no literature needed.
- **How it fails:** A reader expecting the documented absolute correlation instead gets a signed mean; separately the JSON emits an assertive mechanistic claim from an unqualified ratio (e.g. 1.01) with no null comparison. Neither breaks the run.
- **Why it counts as a logic error (not literature):** The finding's headline is a methodology critique, but a genuine code-provable kernel (the abs() comment/code mismatch) survives inside the bundle, so per MIXED-splitting rules the verdict is CODE_LOGIC_ERROR with the interpretation-overstatement recorded as the methodology overlay.
- *Separated methodology overlay (not part of the bug):* The headline complaint — that the JSON hard-codes 'cryptic pocket / intrinsically flexible' for any fold_change>1.0 (line 222) and 'residues move coherently' for any pocket_internal_corr>0 (line 230) with no significance test, effect-size floor, or permutation null — is a statistics/scientific-honesty judgment. The thresholds (>1.0, >0) are legitimate non-degenerate comparisons, so this overlay is METHODOLOGY_ASSUMPTION.

#### ⚪ LOW — BUG‑30: Parser accepts HETATM atoms named 'CA', admitting calcium ions as pseudo-Cα nodes

```python
44:    """Return Cα coords (N,3) and metadata list [{chain, resid, resname}]."""
49:            if not line.startswith(("ATOM  ", "HETATM")):
52:            if atom_name != "CA":
```
- **The bug:** The docstring (line 44) commits the function to returning Cα (alpha-carbon) coordinates, yet line 49 admits HETATM records and lines 51-52 filter on atom_name=='CA' alone with no element-column read. A calcium ion is a HETATM whose atom name is 'CA' and element is 'CA', satisfying both conditions, so it is appended as a coordinate/meta node — a non-Cα atom, contradicting the stated Cα-only intent. Provable from code + docstring plus the input format the parser is explicitly built for.
- **How it fails:** A PDB with a Ca2+ ion -> extra coords/meta row -> extra 3x3 Hessian block, shifted mode spectrum, off-by-one per-residue indexing, inflated n_residues. Latent here: 1W60/8GLA/1AXC are calcium-free, so it changes nothing for the project's real inputs; it triggers only on arbitrary --pdb inputs with hetero atoms named CA.
- **Why it counts as a logic error (not literature):** This is a factual contradiction with the docstring (Cα vs calcium), not a judgment that a better observable exists, so it stays CODE_LOGIC_ERROR. Confidence medium because it is latent for the actual inputs and its recognition leans on PDB-format knowledge.
- *Separated methodology overlay (not part of the bug):* Choosing between an element check (line[76:78]=='C') and an explicit modified-residue (MSE) whitelist, and the fact that recognizing name-'CA' as calcium requires PDB-format awareness, is a minor design consideration.

#### ⚪ LOW — BUG‑31: fold_change and pocket means silently become None if a mean evaluates to 0.0 (falsy-guard)

```python
177:    fold_change  = round(pocket_rmsf / bg_rmsf, 3)    if (pocket_rmsf and bg_rmsf) else None
214:            "pocket_mean_rmsf_norm": round(pocket_rmsf, 4) if pocket_rmsf else None,
226:            "pocket_internal_dccm": round(pocket_internal_corr, 4) if pocket_internal_corr is not None else None,
```
- **The bug:** Lines 177, 214, 215 gate on truthiness ('if (pocket_rmsf and bg_rmsf)', 'if pocket_rmsf', 'if bg_rmsf') instead of 'is not None'. A legitimately computed mean of exactly 0.0 is falsy and is coerced to None, conflating 'computed as zero' with 'not computed'. The code's own sibling line 226 uses the explicit 'is not None' guard, and lines 175-176 use explicit 'else None', proving the intended semantics is None-vs-number — so the truthiness guards are internally inconsistent with the code's own pattern.
- **How it fails:** Degenerate all-zero pocket RMSF -> pocket_rmsf==0.0 -> 'if pocket_rmsf' False -> value replaced with None, and line 177 guard False -> fold_change None, which then cascades into the finding-27 None-format crash. Reachability is low because rmsf_norm is normalized to mean 1.0, but the guard is logically wrong regardless.
- **Why it counts as a logic error (not literature):** A falsy guard that discards a valid 0.0, contradicted by the adjacent 'is not None' guard in the same block, is a self-evident code defect independent of reachability. Verdict stands.
- *Separated methodology overlay (not part of the bug):* None — no scientific judgment is needed to see 0.0 is a valid value that should be kept.


### `md_validation_4070/run_md.py`
<sub>buggy version predates git; verified vs fix `48371e9` + ledger-quoted fragments</sub>

#### 🟠 HIGH — BUG‑32: Advertised RMSD sanity gate absent; NaN run written as DONE via bare json.dumps

```python
L17 `  PBC artifacts / bad analysis                 Sanity gate on RMSD; analysis (analyze_md.py) images first.` (docstring still advertises the gate). Fix ADDED the whole gate: L257 `    # ---- REAL post-run sanity gate: catch blown-up / NaN sims instead of writing them DONE ----`, L263 `    if not math.isfinite(pe):`, L265 `    elif not np.isfinite(final_xyz).all():`, L279-285 write FAILED.json, L302 `    }, indent=2, allow_nan=False))`
```
- **The bug:** The docstring (L17) and the original inline comment advertise a 'Sanity gate on RMSD', but the original run_replicate computed no RMSD and wrote DONE.json unconditionally through a bare json.dumps. A blown-up run has pe/coords = NaN/inf; default json.dumps emits the bare tokens `NaN`/`Infinity` (invalid per the JSON spec, breaking strict downstream parsers), and because DONE.json now exists the corrupt replicate is skipped as 'already complete' on the next run. Doc/comment-vs-code mismatch + NaN-marked-DONE + invalid-JSON are all provable from the code with no appeal to literature. The commit message and the fact that the entire gate block (L257-302) is a fix-time addition confirm the original had no gate.
- **How it fails:** If production blows up, potential energy and coordinates are NaN/inf. The original read pe and wrote DONE.json regardless; json.dumps serialized NaN as the bare token `NaN`, and DONE.json's existence makes the failed replicate be skipped as complete forever, so a numerically failed trajectory silently enters analysis and can never be regenerated.
- **Why it counts as a logic error (not literature):** Confirmed as a self-evident code bug: an advertised check whose code does not exist, plus a bare-json.dumps NaN serialization, both visible from the source and its own docstring. No methodology needed for the core.
- *Separated methodology overlay (not part of the bug):* The refinement that the RMSD must image/unwrap under PBC and superpose onto a stable core before measuring (per the project's MD-correctness rules) is an MD-practice judgment, not part of the core defect.

#### 🟡 MEDIUM — BUG‑34: Resume duplicates DCD frames — coarse checkpoint vs fine DCD cadence

```python
FIXED remediation: L200 `    chk_every = report_every` (L197-199 comment: cadence synced so a resume cannot replay/duplicate a frame written past the last checkpoint). L226 `    sim.reporters.append(CheckpointReporter(str(chk), chk_every))`, L227 `    sim.reporters.append(DCDReporter(str(dcd), report_every, append=append))`, L238 `    chunk = report_every`. Docstring L14 `  n=1 (rep2/rep3 died at the budget wall)      RESUMABLE: a killed run continues, never restarts.`
```
- **The bug:** In the original the DCD was written every report_every (50 ps) while checkpoints landed only every ~500 ps chunk, with the DCD reopened append=True and never truncated. loadCheckpoint rewinds the context step count to the last checkpoint, so frames written after that checkpoint but before the kill are re-simulated and re-appended on resume — duplicated/overlapping frames and a non-uniform time axis. This is a pure file/bookkeeping defect, provable from the reporter/checkpoint cadences alone, and it contradicts the docstring's promise of a clean resume that 'never restarts'.
- **How it fails:** A kill leaves up to ~10 DCD frames past the last checkpoint. On resume, loadCheckpoint rewinds to the checkpoint step and the appended DCDReporter re-writes those same simulated-time windows, so frame index no longer maps linearly to time and any fixed ns/frame analysis mis-timestamps every frame after the first restart.
- **Why it counts as a logic error (not literature):** Mechanical and reproducible: coarse checkpoint cadence + fine DCD cadence + append + no truncation deterministically duplicate frames on resume. The fix (chk_every = report_every) is exactly the remediation. Code bug, no literature needed.
- *Separated methodology overlay (not part of the bug):* The downstream framing that duplicate frames 'flatten or smear the pocket-breathing signal' is analysis-impact interpretation, not part of the code defect.

#### 🟡 MEDIUM — BUG‑35: Equilibration steps counted against production budget; DONE.json mislabels ns

```python
FIXED remediation: L195 `    total_steps = equil_steps + prod_steps` (L193-194 comment: 'Equilibration is NOT charged against the production budget'). L240 `        while sim.context.getStepCount() < total_steps:`. L289 `    production_ns = (sim.context.getStepCount() - equil_steps) * dt.value_in_unit(unit.nanoseconds)` and L291-292 record production_ns (original recorded ns=args.ns).
```
- **The bug:** Original total_steps counted production only (args.ns * steps_per_ns), but equilibration advanced the same context step counter via sim.step(equil_steps) before the production loop, and the loop condition `while getStepCount() < total_steps` includes those equil steps. So with equil 2 ns / ns 100 only 98 ns of production runs, yet DONE.json recorded ns=100. Pure step-arithmetic error, provable with no domain judgment; the fix adds equil_steps to total_steps and records the real production_ns.
- **How it fails:** sim.step(equil_steps) advances the counter to 2 ns before the loop; the loop stops when cumulative (equil+prod) reaches a 100-ns target, so only 98 ns of production is written (~1960 frames) while DONE.json's ns field claims 100 — a fabricated figure that scales with equil_ns.
- **Why it counts as a logic error (not literature):** Off-by-equil_ns is visible from the loop condition and the step accounting alone, and DONE.json's recorded ns contradicts the actual production run. Clear code logic error.
- *Separated methodology overlay (not part of the bug):* None — this is entirely a code/provenance arithmetic error.


### `src/data_processing/fetch_structures.py`
<sub>audited pre-fix source @ `d7cf76d`</sub>

#### 🟠 HIGH — BUG‑37: Advertised chain-count check (layer 3) never enforced

```python
15	  3. Chain count matches expected (PCNA = 3 chains)
139	    chains = {l[21] for l in atom_lines if len(l) > 21}
140	    chain_count = len(chains)
172	    return FetchResult(pdb_id, "ok", path, "passed all checks",
173	                       chain_count, resolution, len(residue_ids), completeness)
```
- **The bug:** Docstring line 15 advertises verification layer 3 as 'Chain count matches expected (PCNA = 3 chains)'. Line 140 computes chain_count, but I scanned every line between 140 and the ok-return (142-173: resolution parse, resolution filter, completeness) and there is NO comparison of chain_count against any expected value — no `if chain_count != ...`, no failed return keyed on chains. The value is only carried into FetchResult (lines 158,170,172-173). The advertised check does not exist in code. This is a self-evident doc-vs-code discrepancy (an 'advertised check whose code does not exist'), provable with zero literature.
- **How it fails:** A single-chain crop, a monomer, or a complex with extra peptide/ligand chains all pass verification given ATOM records, acceptable/waived resolution, and >=90% Ca. chain_count is emitted but never triggers a 'failed' return, so wrong-chain structures flow downstream unflagged.
- **Why it counts as a logic error (not literature):** The docstring makes a promise (layer 3) that the code never keeps; this is a deterministic documented-intent-vs-code mismatch visible from the source alone, matching the CODE_LOGIC_ERROR example 'advertised check whose code does not exist.' The domain-specific fix is an overlay, not the defect.
- *Separated methodology overlay (not part of the bug):* HOW to implement the missing gate correctly — counting PCNA-length protein chains via SEQRES/length instead of raw chain letters, asserting the homotrimer for core IDs, excluding the 1AXC p21 peptide, restricting 8GLA ground truth to chains A+B — is genuine PCNA domain knowledge and is the scientifically correct fix, but it is separable from the code-provable defect.

#### 🟡 MEDIUM — BUG‑38: Cached-file branch discards the verifier verdict; skipped files never stripped

```python
187	    if dest.exists() and not force:
188	        result = _verify_pdb_file(dest, pdb_id)
189	        result.status  = "skipped"
190	        result.reason  = "already exists"
191	        return result
322	        for r in session.ok:
```
- **The bug:** Two code-provable inconsistencies. (1) Line 188 runs the full verifier, which can return status='failed' (e.g. line 136 'no ATOM records'); lines 189-190 then unconditionally overwrite status='skipped' and reason='already exists', discarding the verdict. Running an expensive verification and immediately overwriting its primary output is internally contradictory — either the call is dead work or the overwrite is wrong; either way a corrupt cached file is reported as a benign skip. (2) The --strip loop at line 322 iterates only session.ok, but skipped results are appended to session.skipped (line 108), so on any re-run where files already exist session.ok is empty and no stripped copies are produced. Both are provable from the code with no domain judgment.
- **How it fails:** A truncated cached .pdb that _verify_pdb_file would mark 'failed' is instead reported 'skipped: already exists' and never re-fetched without --force; and every re-run over existing files leaves session.ok empty, so --strip silently produces nothing.
- **Why it counts as a logic error (not literature):** The verify-then-discard and ok-only strip iteration are both deterministic code behaviors inconsistent with the function's own 'Runs verification after download' contract; no literature is needed. CODE_LOGIC_ERROR stands.
- *Separated methodology overlay (not part of the bug):* Whether a corrupt/truncated cached structure should be auto-refetched versus merely flagged is a policy choice, but that overlay is not needed to see the verdict-discard or the strip-loop gap.

#### ⚪ LOW — BUG‑39: Ca completeness threshold: code 90% vs docstring 95%

```python
17	  5. Cα atom completeness (>= 95% of residues have a Cα)
167	    if completeness < 0.90:
169	                           f"Cα completeness {completeness:.1%} < 90%",
```
- **The bug:** Docstring line 17 advertises layer 5 as '>= 95% of residues have a Ca', but line 167 rejects only when completeness < 0.90 and the reason string line 169 also says '< 90%'. This is a direct numeric doc-vs-code threshold contradiction (95 advertised, 90 enforced) — exactly the 'code 0.90 vs doc 0.95 mismatch' archetype, self-evident from the source.
- **How it fails:** A structure with 90-95% Ca completeness passes verification while the documented contract claims a 95% bar, so up to 10% of backbone Ca can be missing under a pipeline that advertises 95%.
- **Why it counts as a logic error (not literature):** Pure numeric doc-vs-code contradiction, provable from three co-located artifacts (line 17 vs 167/169). CODE_LOGIC_ERROR confirmed.
- *Separated methodology overlay (not part of the bug):* Which threshold is scientifically appropriate for backbone completeness (90 vs 95) is a minor domain judgment, but the mismatch itself needs no literature.

#### ⚪ LOW — BUG‑40: Resolution filter silently bypassed for core IDs while docstring claims hard <3.5 A

```python
16	  4. Resolution filter (< 3.5 Å for crystallography)
152	    if resolution is not None and resolution > 3.5:
153	        if pdb_id in PCNA_CORE_IDS:
154	            pass  # ground-truth structures kept regardless of resolution
```
- **The bug:** Docstring line 16 states a hard 'Resolution filter (< 3.5 Å for crystallography)' with no exemption. Lines 152-154 hit a bare `pass` for pdb_id in PCNA_CORE_IDS, retaining those regardless of resolution. 8GLA is a crystallographic structure at 3.77 Å (> 3.5) and is retained by whitelist, so a crystallography structure violates the docstring's stated crystallography filter. Establishing the mismatch needs only the retained resolution (in the data) and arithmetic (3.77 > 3.5) — no scientific judgment — so it does NOT qualify for demotion to METHODOLOGY.
- **How it fails:** A reader trusting the docstring assumes every retained structure is <3.5 Å, but core IDs bypass the gate via `pass` and exit with the generic 'passed all checks' reason (line 172), so the low-resolution keep is not surfaced.
- **Why it counts as a logic error (not literature):** Weaker than #39 (an omission/incomplete summary rather than a flat numeric contradiction), but still a deterministic doc-vs-code inconsistency: a crystallographic 3.77 Å structure is kept under a documented '<3.5 Å for crystallography' filter. Provable from code alone, so CODE_LOGIC_ERROR holds at medium confidence; the auditability/precision framing is a separable methodology overlay.
- *Separated methodology overlay (not part of the bug):* That the 3.77 Å holo weakens the precision of the 6 Å pocket definition, and that the kept-despite-resolution case ought to emit an explicit auditable warning, are scientific/traceability judgments; the whitelist keep itself is intended, self-documented behavior (line 154 comment; PCNA_CORE_IDS defined line 56 as 'always fetch').


### `scripts/phase5_analyze_1axc_md_fixed.py`
<sub>audited pre-fix source @ `0c4bf0e`</sub>

#### 🟠 HIGH — BUG‑42: Homotrimer window selection has no chain filter -> RMSF summaries/ratio pool all 3 chains, n_ca_atoms ~3x

```python
52	def resseq_to_residue_indices(traj, start: int, end: int) -> list[int]:
54	    for r in traj.topology.residues:
59	        if r.is_protein and start <= rs <= end:
60	            out.append(r.index)
162	                              "n_ca_atoms": len(ca),
163	                              "mean_rmsf_nm": float(np.mean(per_atom)),
```
- **The bug:** Independently confirmed: resseq_to_residue_indices (52-61) applies NO chain filter — it loops every traj.topology.residues and matches on resSeq alone. For the PCNA homotrimer, window '239-243' therefore returns residues 239-243 in chains A, B AND C; ca_atoms_for_residues (64-66) yields ~15 CA, so n_ca_atoms (162) reports ~15 for a 5-residue window and mean_rmsf_nm/max_rmsf_nm (163-164) plus the entire ratio_vs_ref table (178-186) average/compare pooled across all three subunits — even though chain_index IS recorded per row at line 155, proving the author knows chains exist yet the aggregation ignores them.
- **How it fails:** No chain filter -> resseq_to_residue_indices returns 3 residue indices per resSeq -> ca_atoms_for_residues yields ~15 CA -> n_ca_atoms=15 and np.mean(per_atom) blends three subunits; the 118-122 reference window is likewise trimer-averaged, so numerator and denominator of ratio_vs_ref each mix three copies.
- **Why it counts as a logic error (not literature):** The task's own MIXED example explicitly names 'residue matching ignores chain so it selects all 3 chains' as a real logic error. The no-chain-filter selection and the ~3x n_ca_atoms count are provable from the code alone (given PCNA is the trimer the whole pipeline processes); the interface-specific interpretation is the separable methodology overlay. Not NOT_REPRODUCIBLE: the analysis is explicitly of the PCNA trimer, so multiple chains with repeated resSeq are the intended input.
- *Separated methodology overlay (not part of the bug):* The claim that pooling 'washes out a real per-interface breathing signal' and that only the A-B interface carries the AOH1996 pocket while chain C is static requires PCNA/AOH1996 site chemistry — a scientific judgment. For a perfectly symmetric homotrimer, averaging 15 equivalent atoms vs 5 is only variance reduction, so the WRONGNESS of pooling (as opposed to the mislabeled count) leans on that domain claim.

#### 🟡 MEDIUM — BUG‑43: usable==0 fallback reverts prod to full (unequilibrated) trajectory yet still emits status 'ok'

```python
129	        usable = max(0, n_total - equil_frames)
130	        incomplete = usable < args.min_frames
137	        prod = traj[equil_frames:] if usable > 0 else traj
159	            summaries.append({"replicate": rep, "window": lbl, "status": "ok",
```
- **The bug:** Confirmed doc-vs-branch inconsistency: docstring FIX 4 (line 11) and fixes_applied (line 203) advertise 'discard equilibration before RMSF' as an applied fix; equil_frames=round(5.0/0.1)=50; line 137's else-branch sets prod=traj (the FULL trajectory including the 50 equilibration frames) whenever usable==0 (n_total<=50), and lines 147-164 then compute RMSF over those unequilibrated coordinates while line 159 still writes status:'ok'. The advertised-always fix is conditionally not applied in that branch.
- **How it fails:** For any replicate with n_total<=50, usable=max(0,n_total-50)=0, line 137 takes the else branch prod=traj, RMSF is computed over all frames incl. equilibration, and status:'ok' is emitted with incomplete_replicate=True as the only marker.
- **Why it counts as a logic error (not literature):** Stripping the MD judgment still leaves a code-provable mismatch: FIX 4 is advertised as applied but the usable==0 branch does not honor it while labeling output 'ok' — analogous to the rubric's '100 ns really 98 ns' doc/code mismatch. Confidence only medium because the branch is conditional (needs a <=50-frame replicate, latent for the 250-frame run) and incomplete_replicate=True mitigates the silence.
- *Separated methodology overlay (not part of the bug):* That the resulting RMSF is 'least trustworthy' and that a consumer filtering on status=='ok' is misled is an MD-practice + usage judgment. Critically, the row simultaneously carries incomplete_replicate=True (160) exactly in this case, so the 'silent mislabel' framing is weaker than presented — status is a computed-vs-not field, and completeness is honestly recorded separately.

#### ⚪ LOW — BUG‑45: Silent core-alignment fallback (core_ca -> all_ca) reintroduces FIX-2 circularity when core < 10; latent

```python
114	        # --- FIX 2: align on stable core = protein CA NOT in any measured window ---
117	        if core_ca.size < 10:
118	            core_ca = all_ca  # fallback
119	        traj.superpose(traj, 0, atom_indices=core_ca)
122	        rmsd = md.rmsd(traj, traj, 0, atom_indices=core_ca)
```
- **The bug:** Confirmed: when core_ca.size < 10 (117) the code reassigns core_ca = all_ca (118), and since md.Trajectory.superpose modifies coordinates in place, superpose (119) then aligns every frame on all_ca — which INCLUDES the window residues being measured — and the aligned coordinates feed the RMSF computation (prod.xyz, 147-151). This directly contradicts the code's OWN FIX-2 comment (114) and docstring (8-9): 'align on ... protein CA NOT in any measured window ... removes circularity.' Provable from the code's stated intent alone, no literature required, and it fires with no flag (only a '# fallback' comment).
- **How it fails:** Triggered only when core_ca.size < 10, i.e. nearly all protein CA fall inside analyzed windows (a truncated model or greatly expanded windows). For the real PCNA trimer, all_ca is hundreds of CA and window_res is ~tens of residues, so core_ca stays in the hundreds and the branch never fires.
- **Why it counts as a logic error (not literature):** Kept as CODE_LOGIC_ERROR, NOT demoted to NOT_REPRODUCIBLE: the offending condition genuinely EXISTS in the source (117-118) and is not contradicted by any other code — it is merely input-gated, and it WOULD fire (and reintroduce circularity) on a truncated topology. NOT_REPRODUCIBLE is reserved for absent/contradicted conditions; input-limited reachability is a severity matter, correctly rated low. The branch's contradiction of FIX 2's explicit comment is a pure code inconsistency needing no domain judgment.
- *Separated methodology overlay (not part of the bug):* That best-fit alignment on measured atoms deflates their apparent RMSF and worsens the 'flat pocket' symptom is a mild domain reading. Also, the finding's stated HARM does not affect current runs — the auditor itself concedes real 1AXC input never reaches this branch.


### `md_validation_4070/analyze_md.py`
<sub>buggy version predates git; verified vs fix `48371e9` + ledger-quoted fragments</sub>

#### 🟡 MEDIUM — BUG‑46: Frame-interval dt hardcoded; comment falsely claims it is read from the log

```python
FIXED file lines 70-71: `def _frame_interval_ns(rep_dir: Path, np, hint: float):` / `"""Read the ACTUAL ns-per-frame from run metadata/log; fall back to hint..."""` and lines 106-107: `# frames -> ns: read the ACTUAL save interval from the run manifest/log (not hardcoded)` / `dt_ns, dt_src = _frame_interval_ns(dcd.parent, np, ns_per_frame_hint)`. Per ledger the original was `dt_ns = ns_per_frame_hint` under a comment 'frames -> ns (read interval from log if present, else hint)' with NO log-parsing code anywhere in the file. (Note: first auditor's code_quote shows an inline '(FIXED: was dt_ns = ns_per_frame_hint...)' annotation that is not literally present; actual line 109 is `equil = int(EQUIL_NS / dt_ns)`.)
```
- **The bug:** The original comment advertised 'read interval from log if present, else hint' but the code unconditionally set dt_ns = ns_per_frame_hint (0.05) with zero log-parsing code, and equil = int(EQUIL_NS/dt_ns) was therefore pinned to 100 frames. An advertised behavior (log reading) that has no corresponding code is a self-evident comment/behavior contradiction, provable from the code alone.
- **How it fails:** The canonical anchor is 'advertised check whose code does not exist': the comment promises log reading, none exists. The downstream harm is a config fact, not literature: a run written with --report-ps 100 (0.1 ns/frame) is ignored, dt_ns stays 0.05, equil=int(5.0/0.05)=100 frames, so 10 ns is discarded instead of 5, silently shifting every post-equil statistic feeding the gate.
- **Why it counts as a logic error (not literature):** CODE_LOGIC_ERROR holds without appeal to literature: a comment states the code reads the interval from the log, and no log-reading code exists in the original. That is exactly the 'docstring says X, code never does X' pattern. The additional wrong-equil harm depends only on the plain fact that report_ps IS the frame save interval, not on any scientific judgment. No demotion warranted.
- *Separated methodology overlay (not part of the bug):* WHICH source dt should come from (mdtraj traj.timestep vs a DONE.json manifest vs the production.log Time column) is an implementation preference; the ledger even notes the manifest may not record report_ps. None of that is needed to see the defect.

#### ⚪ LOW — BUG‑48: Short trajectories silently skip equilibration discard; nominal equil still reported; empty-slice nan

```python
FIXED file lines 110-125: `if n > equil:` / `prod = protein[equil:]` / `else:` ... `print(f"[warn] ... equilibration NOT discarded ...")` / `prod = protein` / `equil_used = 0` and `rmsd_prod = rmsd[equil_used:]` / `if rmsd_prod.size == 0:  # guard against an empty slice -> nan` / `rmsd_prod = rmsd`. Line 239 still: `"equil_ns_discarded": EQUIL_NS`. Per ledger the original was a single-line ternary `prod = protein[equil:] if protein.n_frames > equil else protein` with no warning and an unguarded `rmsd[equil:].mean()`.
```
- **The bug:** Two defects provable from code alone. (1) Empty-slice nan: when n_frames <= equil, the original unguarded `rmsd[equil:].mean()` averages an empty array -> nan lands in rmsd_mean_nm (the fix adds the `rmsd_prod.size == 0` guard). This is the canonical 'unguarded np.mean over a possibly-empty list.' (2) Report/actual mismatch: summary.json hardcodes `equil_ns_discarded = EQUIL_NS` (5.0) even when the short-traj branch discards zero frames.
- **How it fails:** A short/test replicate with n_frames <= 100 (given the pinned 0.05 ns/frame) hits the else branch: prod = protein keeps unsettled frames with no warning, rmsd[100:] is empty so rmsd_prod.mean() -> nan, and summary.json still asserts 5.0 ns were discarded. All three are deterministic from the code.
- **Why it counts as a logic error (not literature):** CODE_LOGIC_ERROR: the empty-slice nan and the constant `equil_ns_discarded` reported against a branch that discarded nothing are both provable without any literature. The equilibration-contamination argument is a separable methodology overlay, not the anchor.
- *Separated methodology overlay (not part of the bug):* The claim that retained early-production frames 'contaminate the openness distribution asymmetrically between apo and holo and bias the gate' is a domain judgment about equilibration effects and is not needed to see the two code defects.


### `src/models/cryptic_gnn.py`
<sub>current source @ `b12c0d4` (unfixed; documented BUG-023)</sub>

#### 🟡 MEDIUM — BUG‑50: PocketGNNXL virtual node global mean-pool has no batch index -> cross-protein pooling under PyG batching

```python
307:        chain_id      : torch.Tensor | None = None,
317:        h_vn  = self.vnode_proj(h_s.mean(dim=0, keepdim=True))    # (1, H)
318:        vn_bc = h_vn.expand(h_s.size(0), -1)                      # (N, H)
319:        vgate = torch.sigmoid(self.vnode_gate(torch.cat([h_s, vn_bc], dim=-1)))
320:        h_s   = h_s + vgate * vn_bc                               # (N, H)
```
- **The bug:** forward (lines 300-308) has no batch parameter and line 317 does h_s.mean(dim=0) over the ENTIRE node tensor. The docstring (line 197-198) advertises 'global protein context' (per-protein), and the file's own sibling symmetry_loss (lines 382-408) explicitly takes a batch arg and packs (batch,resid) keys precisely so 'residues that share a sequence number but belong to different proteins in a batched DataLoader are never mixed' (lines 388-393). The virtual node fails to do the equivalent, so under standard PyG concatenation it averages residues across all proteins in a batch and broadcasts that cross-protein mean back to every residue (318-320). This is a self-evident inconsistency between the stated intent + the file's own batch-aware pattern and the actual code — provable without any literature.
- **How it fails:** Under PyG mini-batching multiple Data objects become one node tensor with a batch index; forward() never receives it, so line 317 averages residues across all proteins in the batch and lines 318-320 inject that cross-protein mean into every residue via the gate, making per-residue scores depend on batch composition — silent because shapes stay valid.
- **Why it counts as a logic error (not literature):** The code-provable core (no batch handling, mean over all nodes) contradicts both the docstring's per-protein 'global protein context' intent and the file's own symmetry_loss which carefully de-mixes proteins by (batch,resid). This is a software/framework-semantics correctness bug, not a scientific judgment, so it stays CODE_LOGIC_ERROR; the only domain-dependent piece (does it corrupt metrics) is correctly isolated in methodology_part. Code condition clearly exists (lines 317, 300-308) so not NOT_REPRODUCIBLE.
- *Separated methodology overlay (not part of the bug):* Whether this measurably corrupts the reported training AUROC depends on the training/eval regime actually using batch_size>1, which is stated outside this file (train default 4). Whether a mean-pool virtual node is even the right global-context design is a modeling choice.

#### ⚪ LOW — BUG‑51: PocketGNN 'homotrimer symmetry prior' never uses chain_id and pulls every residue to the global mean

```python
90:        sym_weight  : float = 0.0,
152:        chain_id      : torch.Tensor | None = None,
170:        # Soft symmetry prior for PCNA homotrimer
171:        if chain_id is not None and self.sym_weight > 0:
172:            h_mean  = h_fused.mean(dim=0, keepdim=True).expand_as(h_fused)
173:            h_fused = h_fused + self.sym_weight * (h_mean - h_fused).detach()
```
- **The bug:** chain_id (line 152) is referenced ONLY in the if-guard (line 171) and never inside the computation (lines 172-173); it is an effectively-dead parameter that gates but does nothing. Line 172 is a plain mean(dim=0) over ALL residues, so no chain/resid grouping happens at all. The comment (line 170) claims 'Soft symmetry prior for PCNA homotrimer'. Both the dead-parameter fact and the comment-vs-code contradiction are readable straight from the two lines with zero domain knowledge.
- **How it fails:** When sym_weight>0 and chain_id is passed, lines 172-173 regularize every residue toward the single global mean vector (and, being mean(dim=0) with no batch arg, across a whole batch), homogenizing embeddings instead of enforcing any A/B/C symmetry. Gated by sym_weight default 0.0 (line 90) so it is dead in the default config and does not affect default results.
- **Why it counts as a logic error (not literature):** The self-evident code facts (chain_id used only in the guard; comment promises a chain-aware homotrimer prior while the code does a global mean with no chain awareness) are provable from the code alone, matching the 'docstring says X but code never does X' and 'dead/unused parameter' CODE_LOGIC_ERROR archetypes. The domain overlay about downstream flattening is correctly separated. The sym_weight=0.0 default limits impact but does not erase the code-logic contradiction.
- *Separated methodology overlay (not part of the bug):* The claims that this global-mean pull specifically 'flattens the score distribution / suppresses pocket-vs-background contrast' and that a correct homotrimer prior must tie residue i of chain A to residues i of chains B/C are modeling/domain judgments about what the prior should do.


### `src/data_processing/parse_pdb.py`
<sub>audited pre-fix source @ `d7cf76d`</sub>

#### 🟡 MEDIUM — BUG‑55: SASA computed over full structure (waters+ligand) and silently defaults to all-zero on any failure

```python
78:        sr.compute(structure, level="R")
83:    except Exception:
84:        pass
109:                sasa=sasa_map.get(key, 0.0),
```
- **The bug:** The bare `except Exception: pass` (lines 83-84) swallows any ShrakeRupley failure, leaving sasa_map empty; line 109 `sasa_map.get(key, 0.0)` then assigns sasa=0.0 to every residue with no log, warning, or sentinel. Because 0.0 is itself a valid 'fully buried' SASA, a genuine computation failure is indistinguishable from real all-buried data — a silent data-integrity defect provable from the code with no appeal to literature.
- **How it fails:** If sr.compute raises for any reason (reachable in real inputs, e.g. degenerate/malformed structures), control jumps to 83-84 and the exception is discarded; sasa_map stays empty and the build loop fills every Residue.sasa with the 0.0 default at line 109, yielding a flat all-zero feature column with no indication of failure. I verified the success path: line 81 populates sasa_map only for het-flag ' ' residues, which standard AAs are, so all-zero cannot arise in the success path — it arises only when the except fires. Manifestation is therefore conditional on an exception (medium confidence), but the silent-mask-with-ambiguous-constant pattern is the code defect independent of the specific trigger. The ledger correctly retracts the 'missing radii element' trigger since ATOMIC_RADII is a defaultdict->2.0.
- **Why it counts as a logic error (not literature):** A competent engineer flags `except Exception: pass` that discards the error and then serves a fallback value indistinguishable from real data as a bug from the code alone — no domain knowledge needed. The occlusion critique is the only part that needs a scientific judgment, so it is split into methodology_part and the masking defect remains CODE_LOGIC_ERROR.
- *Separated methodology overlay (not part of the bug):* Computing SASA on the full parsed structure (line 78, HOH waters and the ligand present as occluders) rather than a protein-only copy — the apo/holo-fairness / occlusion argument for stripping solvent and ligand before compute is a domain judgment about the correct observable, not a self-evident code error.

#### ⚪ LOW — BUG‑56: Insertion codes discarded from residue identity, colliding SASA/secondary-structure map keys

```python
82:                    sasa_map[(chain.get_id(), res.get_id()[1])] = float(res.sasa)
100:            resid = res.get_id()[1]
101:            key = (chain_id, resid)
108:                secondary_structure=ss_map.get(key, 'C'),
109:                sasa=sasa_map.get(key, 0.0),
```
- **The bug:** res.get_id() is (hetflag, resseq, icode) but only index [1] is retained (lines 82 and 100), discarding the icode. Residues 100 and 100A both produce key (chain,100). In the SASA loop (79-82) sasa_map[(chain,100)] is written for res 100 then overwritten for res 100A (last-write-wins), and at lines 108-109 both residue entries look up the same (chain,100) key and receive the single last-written SASA/SS value, so one residue carries the other's features. A plain dict-key-collision provable from the code alone.
- **How it fails:** Both res 100 and res 100A are ATOM records (het-flag ' ') with a CA, so both pass lines 91/93/96 and are appended as two separate Residue entries at line 102 (their ca_coord and b_factor are per-residue correct). Only the map-derived features collide: sasa_map and ss_map are keyed on (chain, resseq) with no icode, so the two residues alias to one SASA and one secondary-structure value, and any downstream (chain,resid) matching cannot distinguish them. Given any PDB input containing insertion codes — a common, valid feature — the collision is deterministic.
- **Why it counts as a logic error (not literature):** The collision is self-evident from the code with no literature appeal; it manifests on ordinary PDB inputs with insertion codes. Conditional-on-input manifestation (like a format-string on a possibly-None value) still qualifies as CODE_LOGIC_ERROR. The impact/benchmark-relevance overlay is correctly separated as methodology.
- *Separated methodology overlay (not part of the bug):* Whether the actual benchmark structures (e.g. 1AXC PCNA:p21) carry insertion codes, and that the ground-truth pocket labeling is coordinate-based (label_pocket_residues, lines 187-206) and therefore unaffected — this is domain/impact context, not needed to see the collision.


### `scripts/dump_cryptic_pocket.py`
<sub>buggy version predates git; verified vs fix `20ba9a7` + ledger-quoted fragments</sub>

#### ⚪ LOW — BUG‑57: holo_mean dead/unused obfuscated variable

```python
Original (ledger L53): holo_mean = float(np.mean([h for *_, h, _ in [(0,)+x for x in rows]])) if rows else float('nan')  -- removed in FIXED; FIXED L64 holo_mean = float(np.mean([h for h, _ in paired])) is a NEW variable consumed at L69 print(f"holo (8GLA) mean matched-pocket score: {holo_mean:.4f}")
```
- **The bug:** The original assigns holo_mean through an obfuscated `(0,)+x` prepend and `*_, h, _` positional unpack, but nothing in the file reads it -- the printed holo mean is recomputed inline on original L56 (np.mean([x[2] for x in rows])). A variable assigned and never consumed is a dead/unused variable, provable from the file alone.
- **How it fails:** Independently confirmed: original L53 holo_mean has no downstream reader (L56 recomputes and prints the same quantity inline), so it is dead code; the `*_, h, _` pattern would also silently pick the wrong tuple column if the layout of `rows` changed. The FIXED file removes the obfuscated assignment entirely and introduces a fresh holo_mean (L64) that is actually printed (L69), corroborating that the original was unused. 'dead/unused variable' is an explicit rubric code-logic example -- no literature needed.
- **Why it counts as a logic error (not literature):** Pure code fact: assigned-but-never-read, verifiable by reading the source with no scientific judgment. Matches the rubric's dead-variable example exactly. Agree with first auditor.

#### ⚪ LOW — BUG‑58: Inconsistent aggregation domain across holo/apo/delta means

```python
Original (ledger): L56 np.mean([x[2] for x in rows]) (holo over ALL rows) ; L57 np.nanmean(apo) (matched only) ; L58 np.mean(deltas) where L51 appends to deltas only when d == d (matched only)  |  FIXED L57 paired = [(h, a) for _, _, h, a in rows if a == a]; L64-66 holo/apo/delta all over `paired`; comment L54-56 'keeps holo_mean - apo_mean == delta_mean exactly'
```
- **The bug:** The summary block prints three related means computed over different residue subsets: holo over all matched-holo rows, apo and delta over the matched-apo subset only. Whenever any GT residue lacks an apo score (apo.get returns NaN at L43), the printed holo_mean - apo_mean does not equal the printed delta_mean. That the three side-by-side summary numbers fail the trivial arithmetic identity delta = holo - apo is an internal inconsistency provable by arithmetic alone.
- **How it fails:** A residue present in holo 8GLA but disordered/absent in apo 1W60 yields NaN from apo.get; it is counted in the all-rows holo mean but excluded from nanmean(apo) and from deltas, so the three printed lines do not reconcile. No PCNA/cryptic-pocket knowledge is required to see a summary whose numbers don't add up -- it is a general reporting/arithmetic inconsistency. The FIXED file computes all three over one shared `paired` list and adds a comment naming the exact invariant it restores, corroborating the original was inconsistent.
- **Why it counts as a logic error (not literature):** The code-provable core (three labeled summary stats that violate delta == holo - apo) needs zero literature -- it is arithmetic. Kept as CODE_LOGIC_ERROR per MIXED handling, with the subset-choice science question split into methodology_part. Confidence dropped to medium because 'internally inconsistent summary' vs 'deliberate mixed-denominator reporting choice' has a subjective edge, but the inconsistency itself is undeniable from code. Agree with first auditor.
- *Separated methodology overlay (not part of the bug):* Whether the scientifically 'preferred' denominator is all holo pocket residues vs the apo-matched subset is a domain/presentation judgment; the auditor correctly isolated this as overlay rather than the defect itself.

#### ⚪ LOW — BUG‑59: Unguarded np.mean over possibly-empty summary lists

```python
Original (ledger): L56 np.mean([x[2] for x in rows]) and L58 np.mean(deltas) called with no empty guard (only the dead L53 holo_mean had `if rows else nan`)  |  FIXED L59-62 if not paired: print("no pocket residues had a valid apo (1W60) match -- holo/apo/delta means undefined (check chain mapping / AOH_GT_BY_CHAIN).")
```
- **The bug:** The printed summary means call np.mean / np.nanmean on lists that can be empty with no guard; np.mean([]) deterministically emits a RuntimeWarning ('Mean of empty slice') and returns NaN. The empty state is reachable: `rows` is empty if no holo residue matches AOH_GT_BY_CHAIN (e.g. unexpected chain encoding), and `deltas` can be empty even when rows is non-empty if no residue has an apo match.
- **How it fails:** With an empty list, np.mean produces a warning and a silent NaN summary that can be misread as a real null result rather than a data-matching failure. Reachability is code-provable, not hypothetical. The FIXED file adds an explicit `if not paired:` branch with a diagnostic message before any mean is computed, confirming the original ran the means unguarded. 'unguarded np.mean over possibly-empty list' is an explicit rubric code-logic example.
- **Why it counts as a logic error (not literature):** Deterministic, code-provable, and reachable -- no literature needed; matches the rubric example verbatim. The fail-loud-vs-explain UX overlay is correctly separated. Agree with first auditor.
- *Separated methodology overlay (not part of the bug):* Whether the empty case should fail loudly via SystemExit or print an explanatory line is a UX preference; the auditor correctly split this from the code-provable unguarded-mean fact.


### `src/evaluation/score_pockets.py`
<sub>audited pre-fix source @ `d7cf76d`</sub>

#### ⚪ LOW — BUG‑62: cluster_pocket_residues returns UNSORTED pockets despite docstring promising 'sorted by mean_score descending'

```python
23:        List of pocket dicts sorted by mean_score descending:
34:    for label in set(labels):
46:    return pockets
```
- **The bug:** Docstring line 23 states the return is 'sorted by mean_score descending', but the function appends pockets in DBSCAN-cluster-label order via `for label in set(labels)` (line 34) and returns at line 46 with no sort operation anywhere in the function. The documented ordering contract is deterministically violated — provable from docstring vs code alone, no literature required.
- **How it fails:** A caller trusting the docstring and taking pockets[0] as the top-mean_score pocket instead receives whichever DBSCAN label came first out of set() iteration — an arbitrary cluster ID, uncorrelated with mean_score. Even if set() iterates small ints ascending, that is label order, not score order.
- **Why it counts as a logic error (not literature):** Independently confirmed: line 23 promises a sort, and lines 34-46 contain no sort call. This is the textbook 'docstring says returns sorted but code never sorts' code logic error. First auditor is correct; no demotion warranted.
- *Separated methodology overlay (not part of the bug):* The added point that the two ranking keys disagree (plain mean_score in docstring vs mean_score*sqrt(size) in rank_pockets) is a design-consistency opinion; the claim that this actively corrupts the 8GLA validation is latent, since no in-repo caller currently consumes this function's output.

#### ⚪ LOW — BUG‑63: write_scored_pdb B-factor guard uses len(line) >= 60 instead of >= 66

```python
76:        if line.startswith('ATOM') and len(line) >= 60:
83:                    line  = line[:60] + bfac + line[66:]
```
- **The bug:** The guard `len(line) >= 60` (line 76) admits ATOM lines of length 60-65, but the rewrite `line[:60] + bfac + line[66:]` (line 83) assumes columns through 66 are present. The guard threshold (60) does not match what the slice structurally requires (>= 66). This is a self-evident guard/slice threshold mismatch, visible from the code alone with no domain judgment.
- **How it fails:** For a length-61 line (60 data chars + the newline kept by splitlines(keepends=True) at index 60), line[:60] discards that trailing newline and line[66:] is empty, so the emitted row is 60 chars + 6-char bfac with no newline and merges with the following line, corrupting the output PDB.
- **Why it counts as a logic error (not literature):** Independently confirmed the condition exists verbatim at lines 76 and 83; no contradicting code makes it unreproducible. To see the defect you only need to notice the guard admits lines shorter than the slice assumes — a code inconsistency requiring no appeal to PDB literature. First auditor is correct; not demotable to METHODOLOGY_ASSUMPTION.
- *Separated methodology overlay (not part of the bug):* The premise that short 60-65-char ATOM lines can actually appear is an input-shape assumption; for standard 80-column PDBs len is always >= 66, so the failure is latent rather than active. But this is an input assumption, not a scientific/methodology critique — the guard/slice inconsistency itself is code-provable.


---

## Part 2 — Reclassified as literature / methodology assumptions (22)

These were in the confirmed ledger but did **not** survive the "is it a bug from the code alone?" test. The code does what it was written to do; calling it wrong requires a scientific/statistical judgment. They may still be worth acting on as *science* — they are simply not code logic errors.

| ID | File | Finding | Why it's a methodology call, not a code bug |
|---|---|---|---|
| 4 | `run_md_analysis.py` | No PBC unwrap/make_whole before alignment | Calling the omission a bug requires the domain judgment that unwrap/make_whole before alignment is standard MD practice, plus the input-dependent assumption that the production DCD actually stored wrapped coordinates (unknowable from code). The proposed fix's own caveats (plain PDB carries no bonds … |
| 5 | `run_md_analysis.py` | DCCM on unaligned coordinates — domain critique; independent code fault is bug 1 | Calling the DCCM 'wrong/degenerate/artifactually all-positive' requires (a) the MD domain principle that cross-correlation analysis must first remove rigid-body motion, and (b) the input-dependent physical assumption that the trajectory actually contains significant global tumbling. Neither is prova… |
| 10 | `parse_trajectory.py` | fraction_open_frames threshold 100 A^3 | The threshold 100.0 is a magic number with no doc/code/sibling reference to contradict it. Calling it 'wrong' requires asserting it fails to discriminate open vs closed, which rests on the domain/geometric premise that convex-hull volumes of Ca clusters are always far above 100 A^3. That premise is … |
| 12 | `parse_trajectory.py` | compute_dccm has no superposition/alignment | compute_dccm gathers raw ca.positions each frame and computes fluctuations about the mean with no superposition/alignment. Calling this wrong requires the MD-domain standard that a DCCM must be computed after removing global rigid-body translation/rotation; otherwise tumbling/drift inflates all corr… |
| 13 | `parse_trajectory.py` | RMSF alignment fits on backbone including pocket residues | AlignTraj fits on select='backbone' (default), which includes the pocket residues whose CA RMSF is then measured. The 'circularity' critique -- that the least-squares fit partially absorbs the pocket's motion, damping measured pocket RMSF and biasing rmsf_ratio toward 1, so the fit set should exclud… |
| 14 | `parse_trajectory.py` | No PBC unwrap/make_whole before alignment or volume | No transformations.unwrap / make_whole / PBC transform is applied in any Universe (load_trajectory, compute_rmsf alignment, compute_dccm, or track_pocket_volume's separate Universe). 'PBC unwrap/make_whole is standard MD post-processing and should be applied' is explicitly a standard-practice requir… |
| 15 | `make_md_figures.py` | RMSF bars plotted on per-chain resid → homotrimer chains overplot at identical x-positions | The load-bearing premise — that the input JSON contains multiple chains with colliding residue numbers because PCNA is a homotrimer whose AOH pocket spans chains A+B — is entirely domain/data knowledge external to this file. Whether a multi-chain system 'should' be faceted/offset vs. plotted on one … |
| 18 | `make_md_figures.py` | Pocket-volume figure renders whole-ring Cα convex hull as 'pocket volume'; only mean/max annotated | The entire load-bearing complaint — that a Cα convex hull over pocket atoms spread across three subunits measures the ~19,700 Å³ whole ring rather than a cavity, is the wrong/near-constant observable, and should be a per-interface cavity or SASA — is a structural-biology judgment. 'Add a min line + … |
| 21 | `graph_construction.py` | rel_pos uses global concatenated-residue index instead of per-chain fractional position | Labelling it wrong requires domain facts: PCNA is a homotrimer of identical chains, rel_pos SHOULD be per-chain for chain-relabeling equivariance, and a monotonic which-third-of-the-ring coordinate can act as a label proxy because AOH1996 positives concentrate on the A-B interface. All of that is sc… |
| 24 | `graph_construction.py` | Explicit chain one-hot encodes subunit identity in a symmetric homotrimer | Calling it a defect requires ML/domain judgment: PCNA is a homotrimer with identical chains, the AOH1996 ground-truth label lives only at the A-B interface (never C), so positives fall in two of three one-hot columns and the feature COULD act as a label proxy / make the model non-equivariant to chai… |
| 29 | `run_nma.py` | ANM cutoff default 7.5 A is a GNM-range cutoff, not an ANM cutoff | Whether 7.5 A (GNM range) vs ~13 A (Atilgan 2001 ANM range) is 'correct', and whether the shorter cutoff under-connects the Ca network and corrupts RMSF/DCCM, is a domain/literature judgment about elastic-network conventions and trimer connectivity. The ledger's own Note concedes 13.0 does NOT fix t… |
| 33 | `run_md.py` | HMR 1.5 amu vs hardcoded 4 fs step — integrator instability | The claim that 1.5 amu is too light to keep a 4 fs Langevin step stable — HMR via constraints=HBonds rigidifies only X-H bonds not H-angle bends, and the standard recipe repartitions to ~4 amu for 4 fs — is an MD integrator-stability / repartitioning judgment requiring domain knowledge. The default … |
| 36 | `run_md.py` | MonteCarloBarostat left unseeded while integrator/velocities are seeded | Calling this a defect requires the domain judgment that exact cross-run reproducibility is a goal. The deterministic per-replicate seed (20260000+rep) is equally explicable as replicate DECORRELATION — giving each replicate distinct initial velocities — which still works with the barostat unseeded. … |
| 41 | `fetch_structures.py` | Residue keys omit insertion codes; None-resolution (NMR/EM) bypasses filter | Calling either a defect requires domain/policy judgment. For the current PCNA crystal core set there are NO insertion codes, so residue_ids and ca_res are complete and the completeness ratio is unaffected — collapsing 100/100A only perturbs the ratio in the rare sub-case where exactly one collapsed … |
| 44 | `phase5_analyze_1axc_md_fixed.py` | incomplete flag absent from window_rmsf.csv — but values correct and flag present elsewhere | The entire severity rests on 'RMSF from a truncated trajectory is systematically biased and pooling it with complete replicates corrupts the per-window mean' — an MD/statistical judgment — applied to a hypothetical external consumer who reads window_rmsf.csv in isolation and group-bys without joinin… |
| 47 | `analyze_md.py` | Pocket SASA sum and Rg mix chains A+B, diluting/conflating the openness signal | Calling it wrong requires the domain judgment that highly solvent-exposed outer-ring residues (25,26,27) carry cavity-state-independent SASA that dilutes the buried signal, that a two-subunit Rg tracks A-B rigid-body separation rather than intra-cavity volume, and that a per-chain / cavity-specific … |
| 49 | `analyze_md.py` | Cohen's d pools autocorrelated frames as independent; reason text overstates rigor | The entire critique -- that 50 ps MD frames are autocorrelated, that the replicate is the independent unit, that frame-pooled SD conflates within- and between-replicate variance, and that 'trustworthy' overstates rigor -- is a statistical/domain judgment. The rubric explicitly lists 'Cohen's d shoul… |
| 52 | `cryptic_gnn.py` | focal_loss uses binary_cross_entropy on sigmoid probabilities instead of logits | Calling it a defect requires the numerical-stability best-practice judgment that heads should emit raw logits and use binary_cross_entropy_with_logits (log-sum-exp stable) to preserve gradient on saturated residues. The ledger itself concedes it is 'not run-breaking due to PyTorch's internal clamp'. |
| 53 | `cryptic_gnn.py` | ranking_loss slices first-N positives/negatives by index rather than sampling randomly | Labeling it a bug requires the training-practice judgment that the subset should be randomized (torch.randperm) so each step sees fresh pairs, plus the data-layout domain assumption that low node indices correspond to chain A (the 'chain-A bias' claim). Both are optimization/domain judgments, not co… |
| 54 | `parse_pdb.py` | Modified standard residues (MSE/SEP/TPO/PTR) stored as HETATM are silently dropped, creating chain gaps | Retaining modified standard residues (MSE->MET, SEP->SER, TPO->THR, PTR->TYR) by mapping the HETATM to its parent canonical AA and keeping the Cα requires crystallography/biochemistry domain knowledge (that SeMet is a MET surrogate that should be counted). The code intentionally admits only the 20 c… |
| 60 | `phase5_pocket_dynamics_1axc.py` | Segment Rg over 5-residue windows as a pocket-breathing metric | The claim that segment Rg 'reports zero dynamics by construction' rests on the biophysical judgment that a short covalently-bonded window's Rg measures internal compactness rather than inter-wall translational separation. The proposed fix (cross-wall CA distances or mouth-residue SASA variance) is a… |
| 61 | `phase5_pocket_dynamics_1axc.py` | Region-sum SASA dilutes CV with buried residues | Whether to report region-summed SASA vs. variance over only pocket-mouth/lining residues (or per-residue max SASA std) is a metric-design/domain judgment about exposing the opening signal without CV dilution. The ledger's own Note admits 'sasa_std_A2 and sasa_range_A2 already carry the opening signa… |

---

## How this was verified

- **Source of truth = real code, not the ledger's prose.** Files rewritten by the fixes were recovered from git: MD/pocket‑dynamics files at `d7cf76d` (pre‑`20ba9a7`), `graph_construction.py` at `20ba9a7` (pre‑`0255fc1`), the two `phase5_*` scripts at `0c4bf0e`, `cryptic_gnn.py` at the current unfixed tip. Three files (`run_md.py`, `analyze_md.py`, `dump_cryptic_pocket.py`) were committed already‑fixed, so their audited defects were confirmed against the ledger's verbatim code quotes plus the remediation present in the fix commits (`48371e9`, `20ba9a7`).
- **Two independent reads per finding.** A classifier and an adversarial verifier each read the same audited source; the adversary was instructed to demote anything resting on domain knowledge and to catch any phantom finding. 5 of 63 verdicts were revised on the adversarial pass.
- **Bar for "logic error":** deterministic wrong/crashing/degenerate behavior or a self‑contradiction with the code's own stated intent, provable without MD/ML literature. Bundled findings were split: the code‑provable core is the bug; the "better science" overlay is recorded but not counted.
