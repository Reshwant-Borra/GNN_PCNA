# docs/visuals/ — Visualization System

## Files

| File | Content | Format |
|---|---|---|
| `system_map.mmd` | Full AI + research operating system (NLM → Claude → Gemini → ChatGPT) | Mermaid flowchart |
| `pipeline_map.mmd` | PCNA pipeline stages 1–7 | Mermaid flowchart |
| `data_flow.mmd` | Data transformation: PDB → graphs → model → MD → results | Mermaid flowchart |
| `experiment_flow.mmd` | Experiment lifecycle (idea → plan → implement → log) | Mermaid flowchart |
| `knowledge_graph_map.mmd` | Obsidian brain node structure and connections | Mermaid graph |
| `system_map.html` | Interactive canvas: all pipeline nodes with hover details | HTML + Canvas |

## Open System Map (Windows)
```powershell
start docs\visuals\system_map.html
```

## Rendering in Obsidian

Obsidian renders `.mmd` files natively as Mermaid diagrams if you enable the **Mermaid** core plugin:

1. Open **Settings → Core plugins → Mermaid diagrams** → toggle ON
2. Create a note and embed any diagram with:

````markdown
```mermaid
%%paste contents of .mmd file here%%
```
````

Or, if you have the **Obsidian Mermaid** community plugin, `.mmd` files render inline when linked.

### Quick embed example

To embed `system_map.mmd` content in a note:

````markdown
```mermaid
flowchart TD
    ...paste system_map.mmd contents...
```
````

## Rendering Outside Obsidian

- **VS Code**: Install "Markdown Preview Mermaid Support" extension → preview any `.md` with mermaid blocks
- **CLI**: `mmdc -i system_map.mmd -o system_map.svg` (requires `@mermaid-js/mermaid-cli`)
- **Browser**: Open `system_map.html` directly — no install needed
