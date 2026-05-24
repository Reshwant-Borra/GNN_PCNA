# Module Contracts

## Base Agent

```python
class BaseAgent:
    agent_id: str
    display_name: str
    def run(self, context: ContextPacket) -> AgentOutput:
        ...
```

Must return AgentOutput, record evidence, avoid direct canonical memory mutation, and request human review when needed.

## Context Packet

```python
class ContextPacket:
    task: str
    intent: list[str]
    risk_level: str
    memory_files: list[Path]
    registry_entries: dict
    repo_files: list[Path]
    artifacts: list[Path]
    known_risks: list[str]
    allowed_actions: list[str]
    forbidden_actions: list[str]
    expected_output_schema: str
```

## Orchestrator

```python
class Orchestrator:
    def route(self, user_message: str) -> OrchestrationPlan: ...
    def execute_plan(self, plan: OrchestrationPlan) -> WorkflowResult: ...
```

Must classify intent, select agents, determine gates, detect human approval needs, build context packet, and block failed gates.

## Registry Store

```python
class RegistryStore:
    def load(self, name: str) -> dict: ...
    def validate(self, name: str) -> list[str]: ...
    def append(self, name: str, entry: dict) -> str: ...
    def update(self, name: str, entry_id: str, patch: dict) -> None: ...
```

Use atomic writes and never destructively delete entries.

## Error Handling

- Missing file: blocked.
- Invalid JSON: fail.
- Missing critical dependency: fail.
- Critical test skip: fail.
- Incomplete provenance for paper artifact: fail or high warning.
