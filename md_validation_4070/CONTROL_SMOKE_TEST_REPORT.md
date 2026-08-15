# Control Smoke Test Report

Status: NOT_RUN

Required command:

```bash
./md.sh smoke
```

Result: Exact required 0.1 ns control smoke has not been executed in md_validation_4070/outputs. Zero-production preflight was run separately and is not scientific evidence.

Preflight completed in `preflight_outputs_min5000` with zero production steps. That validates assembly, PDBFixer repair, solvation, parameterization, long-bond assertions, and default minimization, but it does not validate trajectory output, NaN-free dynamics, frame count, PBC handling, or analysis compatibility.
