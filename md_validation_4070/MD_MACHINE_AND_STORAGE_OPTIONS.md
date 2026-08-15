# MD Machine And Storage Options

## RTX 4070

Intended for smoke testing, 3 x 5 ns control-first validation, and local benchmarking/validation. Use the conda environment in `environment.yml`; keep trajectories on fast local NVMe during runs, then archive DCD/topology/checkpoint/log/provenance hashes.

## M5 Mac

Good for report generation, static validation, code checks, and lightweight preparation/audits when practical. Not intended for production MD. CUDA is not available.

## Cloud GPUs

Intended for production MD and potentially parallel independent replicates. Benchmark the chosen cloud GPU before extrapolating runtime. Prefer independent single-GPU replicate jobs unless the implementation explicitly supports something else. Record cloud provider, instance type, GPU model, driver, CUDA, OpenMM platform, image/container hash, costs, and storage location.

Use persistent storage. tmux protects against SSH disconnects but not instance termination; checkpoints only survive if the underlying storage survives. Preserve trajectories/results before destroying an instance.

## Storage

Plan for topology/checkpoint/log/provenance plus DCD trajectories. At 50 ps output, 100 ns gives about 2000 frames per replicate. For about 155k atoms, uncompressed DCD can be several GB per 100 ns replicate; six production replicates can plausibly require tens of GB before derived analyses. Keep at least 200 GB free working space for production plus backups, and register hashes for every non-committed large artifact.
