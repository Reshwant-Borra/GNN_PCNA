# Simulation Protocol

Current executable workflow:

```text
GNN frozen -> structure/preparation validation -> MD parameter validation -> frozen analysis -> 0.1 ns smoke -> analysis validation -> 3 x 5 ns control-first validation -> human Gate-6 -> benchmark on chosen production GPU -> production MD -> frozen final analysis
```

Use the repository launcher from the root:

```bash
./md.sh smoke
./md.sh status
./md.sh attach
./md.sh control5
./md.sh benchmark
./md.sh production
./md.sh analyze
```

Production remains blocked until Gate-6 human approval is recorded. Production plan, if approved, is 3 x 100 ns 8GLA control plus 3 x 100 ns 1W60 apo/candidate, 600 ns aggregate.

Current parameter source of truth: `md_validation_4070/run_md.py`; practical instructions: `md_validation_4070/FINAL_MD_EXECUTION_INSTRUCTIONS.md`; current status: `PROJECT_STATUS.md`.
