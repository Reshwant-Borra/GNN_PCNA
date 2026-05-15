# CHANGELOG.md — What Changed and When

> Add entries at the top. One entry per meaningful change.

---

## 2026-05-15 — PocketGNN v2 + full pipeline

**Changed by:** Advay

### Summary
Complete model redesign, data crawler, Obsidian vault, Streamlit UI, MCP server, and 6 bug fixes.

### Model (src/models/cryptic_gnn.py)
- **PocketGNN v2**: dual-branch GATv2Conv (spatial + sequential), gated fusion, 10.4M params
- Node features 26→40; edge features 2→6; 3-layer pre-encoder; 4-layer MLP head
- Three size configs: `PocketGNN()` large / `.medium()` / `.small()`
- Loss: focal + ranking + symmetry (PCNA finetune only)
- CrypticGNN v1 preserved for comparison
- Bug fixes: `sym_weight` default changed 0.1→0.0 (global mean prior was semantically wrong); added `param_count()` to CrypticGNN

### Data pipeline (src/data_processing/)
- `graph_construction.py`: `build_graph_v2()` — dual-graph Data with 40-dim nodes, 6-dim edges, pseudo-dihedrals, interface flag, chain encoding
- Vectorized `_build_backbone_edges()` (was O(N²) Python loop)
- Vectorized `is_interface` computation (was O(N²) Python loop)

### Crawler (agents/pcna_crawler.py)
- 13-domain crawler: RCSB, PDBe, AlphaFold, SIFTS, UniProt, NCBI, InterPro, Zenodo, GitHub, PubMed, bioRxiv, PubChem, ChEMBL
- 5-layer validation: network, format, structural, biological, provenance (SHA-256)
- Outputs `data/catalog/raw_catalog.json`

### Obsidian vault (docs/vault/)
- 160 linked notes: structures, papers, datasets, compounds
- YAML frontmatter, wikilinks, relevance scores
- `KNOWLEDGE_GRAPH.md` root node

### MCP server (agents/mcp_server.py)
- FastMCP server exposing vault + model inference to Claude Code
- 8 tools: list_structures, get_structure, search_vault, list_papers, list_datasets, get_knowledge_graph, run_inference, get_pipeline_status
- Configured in `.claude/mcp.json`

### Training (src/training/train.py)
- Added `--model_size`, `--resume`, `--phase` (pretrain/finetune) CLI args
- Checkpoint now saved by best AUROC (not loss)
- Finetune phase enables symmetry loss

### UI (src/ui/app.py)
- Streamlit app: sequence heatmap, top-residue table, chain symmetry check
- B-factor PDB export (PyMOL-ready) + CSV download
- Fixed: B-factor line guard for short PDB lines

### Docs
- README.md: full rewrite for v2 with quick-start commands
- KNOWN_BUGS.md: all 6 bugs documented and marked resolved
- CHANGELOG.md: this entry

---

## 2026-04-30 — System Initialized

**Changed by:** Claude Code (initial setup)

### System created
- Full AI-assisted research operating system initialized
- Multi-agent workflow established: NotebookLM MCP → Obsidian Brain → Claude → Gemini → ChatGPT
- Obsidian Markdown brain selected as persistent project context

### Files created (new)
- `docs/knowledge/INDEX.md` — root brain node
- `docs/knowledge/RESEARCH_QUESTION.md`
- `docs/knowledge/BIOLOGY_PCNA.md`
- `docs/knowledge/VALIDATION.md`
- `docs/knowledge/AI_WORKFLOW_RULES.md`
- `docs/knowledge/NOTEBOOKLM_WORKFLOW.md`
- `docs/knowledge/VISUALIZATION_SYSTEM.md`
- `docs/experiments/EXPERIMENT_INDEX.md`
- `docs/experiments/experiment_template.md`
- `docs/experiments/E001_baseline_gnn.md`
- `docs/experiments/E002_pcna_pocket_prediction.md`
- `docs/experiments/E003_md_validation.md`
- `docs/data/DATA_INVENTORY.md`
- `docs/data/DATA_SCHEMA.md`
- `docs/data/PDB_STRUCTURES.md`
- `docs/data/PROCESSED_DATA.md`
- `docs/data/DATA_PROVENANCE.md`
- `docs/implementation/ARCHITECTURE.md`
- `docs/implementation/FILE_GUIDE.md`
- `docs/implementation/COMMANDS.md`
- `docs/implementation/ENVIRONMENT.md`
- `docs/implementation/TESTING.md`
- `docs/plans/README.md`
- `docs/plans/plan_template.md`
- `docs/prompts/CLAUDE_PLANNER_PROMPTS.md`
- `docs/prompts/GEMINI_IMPLEMENTER_PROMPTS.md`
- `docs/prompts/CHATGPT_REVIEW_PROMPTS.md`
- `docs/prompts/NOTEBOOKLM_EXTRACTION_PROMPTS.md`
- `docs/notebooklm/README.md`
- `docs/notebooklm/extraction_template.md`
- `docs/notebooklm/distilled_notes/pocketminer_notes.md`
- `docs/notebooklm/distilled_notes/deepallo_notes.md`
- `docs/notebooklm/distilled_notes/pcna_biology_notes.md`
- `docs/notebooklm/distilled_notes/md_validation_notes.md`
- `docs/logs/DECISIONS.md`
- `docs/logs/BUG_LOG.md`
- `docs/logs/CHANGELOG.md`
- `docs/logs/RESEARCH_NOTES_LOG.md`
- `docs/visuals/experiment_flow.mmd`
- `docs/visuals/knowledge_graph_map.mmd`

### Files updated (existing)
- `REPO_MAP.md` — expanded to full system map with do-not-scan list and task lookup
- `CLAUDE.md` — full rewrite with planning rules, cost-saving rules, role separation
- `AGENTS.md` — full rewrite with detailed handoff protocol and copy-pasteable blocks
- `docs/visuals/README.md` — updated for new diagrams
- `docs/visuals/system_map.html` — updated with AI workflow nodes
- `docs/visuals/system_map.mmd` — updated for full AI + research system

---

## Template

```
## YYYY-MM-DD — {Short title}

**Changed by:** {who/what made this change}

### Summary
{One paragraph}

### Files changed
- `path/to/file` — what changed
```

---

## Related

[[BUG_LOG]] · [[DECISIONS]] · [[EXPERIMENT_INDEX]] · [[INDEX]]
