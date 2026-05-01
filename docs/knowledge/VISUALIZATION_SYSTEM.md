# VISUALIZATION_SYSTEM.md — Visual Layer

→ Links: [[SYSTEM_OVERVIEW]] | [[PIPELINE]] | [[AI_WORKFLOW_RULES]]

---

## Available Visuals

| File | Content | Format |
|---|---|---|
| `docs/visuals/system_map.mmd` | Full AI + research system (NLM → Claude → Gemini → ChatGPT) | Mermaid flowchart |
| `docs/visuals/pipeline_map.mmd` | PCNA pipeline stage-by-stage | Mermaid flowchart |
| `docs/visuals/data_flow.mmd` | Raw data → processed → graphs → model → MD → output | Mermaid flowchart |
| `docs/visuals/experiment_flow.mmd` | Experiment lifecycle: idea → plan → implement → log | Mermaid flowchart |
| `docs/visuals/knowledge_graph_map.mmd` | Obsidian brain structure + inter-file connections | Mermaid graph |
| `docs/visuals/system_map.html` | Interactive canvas visualization (all pipeline nodes) | HTML + Canvas |

---

## How to Open Visuals

### Interactive HTML (system_map.html)
```powershell
start docs\visuals\system_map.html
```
Features: drag to pan, scroll to zoom, hover for node details.

### Mermaid files in Obsidian
1. Open vault in Obsidian
2. Open any `.mmd` file (or copy content into a `.md` code block with ```mermaid)
3. Obsidian renders Mermaid natively (no plugin needed in newer versions)
4. Or install the "Mermaid" plugin from Obsidian community plugins

### Mermaid CLI (optional, offline)
```bash
npx @mermaid-js/mermaid-cli -i docs/visuals/pipeline_map.mmd -o pipeline_map.png
```
Mark as optional: requires Node.js and mmdc installed.

### VS Code
- Install extension: "Markdown Preview Mermaid Support"
- Preview any .mmd file or inline Mermaid in .md files

---

## What Each Visual Means

### system_map.mmd
Shows the full AI-assisted research operating system:
- NotebookLM → Obsidian Brain → Claude → Gemini → ChatGPT
- Parallel: raw research extraction pipeline
- Use when explaining the system to a new collaborator

### pipeline_map.mmd
Shows the PCNA data processing pipeline stage by stage (7 stages).
Use when planning which stage to implement next.

### data_flow.mmd
Shows how data transforms at each stage:
`PDB files → cleaned PDB → PyG graphs → model outputs → MD outputs → results`
Use when debugging data pipeline issues.

### experiment_flow.mmd
Shows the lifecycle of a single experiment:
`idea → plan file → Gemini implement → run → evaluate → log → next`
Use when planning or reviewing the experiment process.

### knowledge_graph_map.mmd
Shows the Obsidian brain structure:
`INDEX.md` as center, connected to all knowledge files, experiments, data docs.
Use to understand the brain topology.

### system_map.html
Interactive draggable canvas showing all pipeline nodes with hover details.
Use for exploring the technical pipeline visually.

---

## Obsidian Graph View

When you open the project as an Obsidian vault, the `[[wikilinks]]` throughout `docs/` create an automatic knowledge graph.

**Key hubs (highest connectivity):**
- `INDEX.md` — links to everything
- `PIPELINE.md` — linked by data, model, validation docs
- `EXPERIMENT_INDEX.md` — links to all experiments

To see the graph: Obsidian → Graph View (Ctrl+G or Cmd+G)

---

## Adding New Visuals

1. Create `.mmd` file in `docs/visuals/`
2. Use `flowchart TD` or `flowchart LR` syntax
3. Add entry to `docs/visuals/README.md`
4. Add entry to this file
