# DECISIONS.md — Architecture Decisions Log

> Never delete entries. Add new entries at the top.

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
