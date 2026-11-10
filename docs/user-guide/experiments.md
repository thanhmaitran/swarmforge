# Experiments

```bash
python experiments/runners/run_experiment.py --config experiments/scenarios/scalability.yaml --profile quick
python experiments/runners/batch_runner.py --profile quick            # all eight
python experiments/runners/batch_runner.py --workers 4                # full grids
python experiments/analysis/generate_report_assets.py                 # tables + figures from results
```

An experiment YAML has `kind` (`simulation`, `mapf`, `allocation`), `seeds`, a `factors` grid, optional named
`variants` (bundles of overrides), fixed `overrides`, `metrics` and `profiles` (e.g. `quick`) replacing parts of
the specification. Output under `experiments/results/`:

* `raw/<name>.csv|jsonl` - one record per run, including `valid` and `status` (errors are recorded, not hidden);
* `aggregated/<name>.csv|json` - n, mean, median, SD, 95% CI, IQR per factor level and metric;
* `metadata/<name>.json` - git commit, Python/OS/hardware, compiler, experiment hash, timestamp.

Comparisons between algorithms use the *same* scenario and seed (paired design); see
[methodology](../research/experimental-methodology.md).
