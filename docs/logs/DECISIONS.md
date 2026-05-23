# DECISIONS.md — Architecture Decisions Log

> Never delete entries. Add new entries at the top.

---

## D006: PCNA claim downgraded to residue prioritization

**Date:** 2026-05-23
**Decision:** Final PCNA reporting must use the clean-split `xl_esm_full` checkpoint and frame results as ESM2-augmented residue prioritization / hypothesis generation, not hidden-pocket discovery.

**Rationale:**
- Regenerated PCNA outputs show the top `1W60` cluster is only 4 residues with mean score 0.710175.
- The top `1W60` cluster overlaps only 3 residues from the MD/AOH-region residue set.
- The full AOH1996/MD pocket is not recovered as a thresholded cluster.
- `8GLA`, the AOH ligand-bound positive-control structure, has no thresholded DBSCAN cluster under the regenerated clean-split checkpoint.
- Previous broad AOH-region recovery was tied to deprecated pre-clean-split reporting and must not be reused.

**Alternatives considered:**
| Option | Rejected reason |
|---|---|
| Keep "hidden pocket discovery" claim | Regenerated clean-split outputs do not recover a full pocket |
| Treat the top `1W60` cluster as AOH1996 recovery | It is a sparse 4-residue signal and misses most of the AOH/MD contact region |
| Use old PCNA figures for continuity | They are based on superseded checkpoints/metrics and changed materially after clean regeneration |

**Source:** E005 PCNA `xl_esm_full` regeneration and final framing audit.

---

## D005: Clean benchmark framing is ESM2-augmented exploratory signal

**Date:** 2026-05-22
**Decision:** Report `xl_esm_full` as the best clean-split condition, but frame the result as ESM2-augmented exploratory signal rather than pure structural cryptic-pocket validation.

**Rationale:**
- Final clean split best condition is `xl_esm_full`: test AUPRC 0.2513 (95% CI 0.1267-0.3815), AUROC 0.8649.
- Geometry-only XL is lower: AUPRC 0.1923, AUROC 0.8325.
- ESM-zero XL is weaker: AUPRC 0.1071, AUROC 0.6815.
- The gap between full ESM2 and ESM-zero means sequence context is a major contributor.

**Alternatives considered:**
| Option | Rejected reason |
|---|---|
| Claim pure structural-learning validation | ESM-zero ablation is too weak to support that framing |
| Use old random-split AUROC headline | Homology leakage invalidated that split |

**Source:** E004 final clean-split ablation suite.

---

## D001: GATv2Conv over GCNConv for GNN layers

**Date:** 2026-04-30
**Decision:** Use GATv2Conv (4 layers, 256 hidden, 4 heads) as the primary GNN layer.

**Rationale:**
- Dynamic attention (score computed jointly from both node representations) captures long-range interactions better than GCNConv
- Edge features can be incorporated at each message-passing step
- Residual connections added to prevent over-smoothing at 4 layers

**Alternatives considered:**
| Option | Rejected reason |
|---|---|
| GCNConv | No dynamic attention; cannot incorporate edge features natively |
| GINEConv | Less interpretable attention; less literature precedent for protein graphs |
| TransformerConv | Higher memory cost; overkill for 800-node graphs |

**Source:** Initial architecture decision (2026-04-30). See `docs/knowledge/MODELS.md`.

---

## D002: Focal Loss over weighted BCE

**Date:** 2026-04-30
**Decision:** Use Focal Loss (γ=2, α=0.25) as default training loss.

**Rationale:**
- PCNA has severe class imbalance (~5–15% pocket residues)
- Focal loss down-weights easy negatives, forcing model to focus on hard examples
- Standard in object detection literature; validated for molecular binding site prediction

**Alternatives considered:**
| Option | Rejected reason |
|---|---|
| Weighted BCE | Less effective for severe imbalance; focal loss is strictly better |
| Dice loss | Designed for segmentation; less principled for residue scoring |

---

## D003: Obsidian Markdown as persistent project brain

**Date:** 2026-04-30
**Decision:** Use `docs/knowledge/` Markdown files as the persistent Claude context, not a database or embedding store.

**Rationale:**
- Markdown files are readable by Claude, Gemini, ChatGPT, and humans equally
- No infrastructure needed — just files in the repo
- Obsidian wikilinks create a queryable knowledge graph for free
- Compact structured files (tables, bullets) minimize Claude token usage per session

---

## D004: Multi-agent workflow (Claude → Gemini → ChatGPT)

**Date:** 2026-04-30
**Decision:** Claude plans, Gemini implements, ChatGPT reviews.

**Rationale:**
- Claude has strong reasoning but expensive context budget
- Gemini has large context window — ideal for full-file implementation
- ChatGPT has strong code review capabilities
- Separating roles prevents any single agent from accumulating too much context

---

## Template for new decisions:

```
## D{NNN}: {short title}

**Date:** YYYY-MM-DD
**Decision:** {one sentence}

**Rationale:**
- ...

**Alternatives considered:**
| Option | Rejected reason |
| | |

**Source:** {who made this decision and why}
```

---

## Related

[[MODELS]] · [[AI_WORKFLOW_RULES]] · [[CHANGELOG]] · [[ARCHITECTURE]] · [[BUG_LOG]]
