---
type: analysis-report
track: 5
author: Advay (parallel track)
date: 2026-05-28
status: complete
phase3_dependency: none
---

# Heuristic Pocket-Score Analysis

Analysis of the `heuristic_pocket_score` field in `data/registries/friend_crawl_registry.json`
and its source data. **No scientific claims** — the heuristic is a weak prior signal from a
non-frozen pipeline, not the Phase 3 model, and not a druggability or novel-site claim
(governance docs 12, 14).

Reproduce with: `python scripts/analyze_heuristic_scores.py`
Machine-readable stats: `reports/phase4/heuristic_score_stats.json`
Figures: `reports/phase4/figures/`

---

## 5b — What the heuristic score represents (documented, not assumed)

The provenance below is established by direct inspection, not recall:

| Question | Finding | Evidence |
|---|---|---|
| What generated it? | A **prior GNN inference pass** that produced per-residue cryptic-pocket scores, aggregated per structure. | `data/registries/friend_feature_schema.json` → feature `pocket_heuristic_scores`: *"Per-structure heuristic cryptic pocket scoring from GNN inference pass"* |
| What is the registry field exactly? | `heuristic_pocket_score` = the **`mean_score`** column of `data/results/all_structures_scores.csv`. Verified exact match for all 4 scored structures (1AXC 0.1147, 1W60 0.133, 8GLA 0.1324, 1W61 0.0536). | Cross-check in `scripts/analyze_heuristic_scores.py` / direct CSV read |
| Per-structure or per-residue? | **Per-structure aggregate** (mean of per-residue scores). The CSV also carries `std_score`, `max_score`, `pct_above_0.4`, `pct_above_0.5`, `n_pockets`, `top_chain`, `top_resid`. | CSV header |
| What does 0.0 vs 1.0 mean? | Scores are per-residue cryptic-pocket probabilities in **[0, 1]**; the per-structure mean is therefore also in [0, 1]. Observed `mean_score` range across the 90-row CSV is **0.0202 – 0.2159** (means are low because most residues are not pocket-like). Higher = more residues scored pocket-like on average. | CSV min/max |
| What inputs did it use? | Same processed structures + ESM-2 embeddings used elsewhere in the friend pipeline (per the schema, ESM-2 `esm2_t30_150M_UR50D`-class, 480-dim). | `friend_feature_schema.json` |

### Known limitations (must carry into Phase 4 framing)

1. **It is itself a model output, not a physics-based pocket detector.** It comes from a
   prior, **non-frozen, non-governed** GNN pass — distinct from the Phase 3 frozen model.
   It must not be conflated with Phase 3 predictions or used to validate them.
2. **It is a per-structure mean.** A mean collapses all residue-level signal; a structure
   with one strong pocket and a structure with diffuse weak signal can share a mean. Use
   `max_score` / `pct_above_0.5` if residue-level discrimination is needed.
3. **Coverage is sparse in the governed registry.** Only **4 / 72** structures carry a
   non-null score (see below).
4. **No calibration / no ground truth for PCNA.** The CSV `auroc` column is only populated
   for rows with `has_labels=true`; the 4 PCNA rows are unlabeled, so no AUROC exists for
   them. Treat the score as uncalibrated.

---

## 5a — Distribution analysis

### Coverage: only 4 of 72 registry structures are scored

This contradicts the Track-5 brief's assumption of "scores (0.05–0.18 range) across all 72
structures." **68 of 72 registry records have `heuristic_pocket_score = null`.** The 4
scored records are exactly the 4 CSV rows flagged `is_pcna=True`:

| PDB ID | heuristic_pocket_score | resolution (Å) | chain_count | role |
|---|---|---|---|---|
| 1W61 | 0.0536 | 2.10 | 2 | scored |
| 1AXC | 0.1147 | 2.60 | 6 | scored (top non-control candidate, Track 2) |
| 8GLA | 0.1324 | 3.77 | 4 | **AOH1996 positive control** |
| 1W60 | 0.1330 | 3.15 | 2 | scored |

Figure: `figures/registry_scores_bar.png`.

**Why the other 68 are null:** the friend scoring pass only propagated `mean_score` into the
registry for rows its pipeline flagged `is_pcna=True` (4 rows). The remaining 68 PCNA-catalog
structures were never scored by that pass (they do not appear in `all_structures_scores.csv`
at all — 66 of the 72 catalog IDs are absent from the CSV). This is a **coverage gap in the
prior pipeline**, not a property of those structures. It cannot be back-filled here without
re-running a scoring pass, which is out of scope (no inference outside the gated Phase 3/4
path).

### Score vs resolution / chain_count

With only n=4 scored registry structures, **no correlation can be asserted** (figure
`figures/registry_score_scatter.png` shows the 4 points for transparency only). Reporting a
trend on n=4 would violate claim policy.

### Broader context: the 90-row CSV (4 PCNA + 86 extended-set)

For distributional context only, the full `all_structures_scores.csv` (90 structures: 4 PCNA
+ 86 non-PCNA extended-set, see Track 2 ESM validation) gives:

| Statistic | mean_score |
|---|---|
| min | 0.0202 |
| Q1 | 0.0416 |
| median | 0.0537 |
| Q3 | 0.0758 |
| max | 0.2159 |

Figure: `figures/csv_score_distribution.png`. **Caveat:** 86 of these 90 rows are not PCNA
and not part of the governed crawl; this distribution is background, not a PCNA result.

### 8GLA positive-control position

The brief asks whether the AOH1996 positive control (8GLA) sits in the top quartile *if the
heuristic is meaningful*. Observations (not claims):

- Among the **4 scored PCNA structures**, 8GLA (0.1324) is the **2nd highest of 4** (just
  below 1W60's 0.1330).
- In the **90-structure CSV** distribution, 8GLA is at the **~92nd percentile** and above Q3
  (0.0758), i.e. **in the top quartile / roughly top decile**.

This is **consistent with** the heuristic carrying some weak signal at the positive control,
but n=4 PCNA scores and an uncalibrated, non-frozen source mean this is an **observation for
context only** — it does not validate the heuristic, the positive control, or any prediction.

---

## Phase 4 hand-off note

When the Phase 3 model is frozen and PCNA inference is gated open (GATE 6), the question of
whether frozen-model predictions correlate with this heuristic should be evaluated on the
4 scored structures with explicit acknowledgement of the n=4 limitation, using the
residue-level CSV columns (`max_score`, `pct_above_0.5`) rather than the per-structure mean
where residue resolution matters. Any comparison must be framed as same-data computational
comparison, never as validation.
