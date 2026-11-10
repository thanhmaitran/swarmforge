# ADR-0005: Reproducible experiments

## Status
Accepted

## Decision
* Every run is a pure function of (configuration, seed); RNG streams are derived with `SeedSequence`.
* Algorithm comparisons use identical scenarios and seeds (paired design).
* Raw records are kept (CSV + JSONL) with `status` and `valid`; failures are recorded, never skipped.
* Each experiment stores metadata (git commit, dirty flag, Python, OS, CPU count, compiler, experiment hash, timestamp).
* A regression suite pins metrics of fixed scenarios; behaviour changes must update `golden.json` knowingly.
* No result appears in documentation unless it came from a recorded run.

## Consequences
Runs can be repeated and explained. Wall-clock measurements (runtimes) are inherently machine-dependent and are
reported with the hardware in the metadata; simulated quantities are exactly reproducible.
