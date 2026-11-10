# Experimental methodology

* **Scenarios and seeds.** Each factor combination is run for every seed; comparisons between algorithms pair runs
  that share scenario and seed. The *full* profile of every specification uses 10 seeds; the *quick* profile (used for
  the checked-in results) uses 3-5 seeds and reduced grids - the exact grids are in each YAML.
* **Metrics.** Completion rate \(R_c = N_{completed}/N_{created}\); completion time = creation -> completion;
  execution time = start -> completion; throughput = completed / simulated time; plus distance, planning runtime,
  safety events (three kinds), waits, deadlocks, energy, charging utilisation, workload CV, message counts.
* **Statistics.** Mean, median, SD, 95% CI (Student t), IQR per cell; paired t-test / Wilcoxon and Cohen's \(d_z\)
  (`experiments/stats.py`). With \(n \le 5\) seeds, intervals are wide: treat quick-profile results as
  indicative, not conclusive, and prefer effect sizes over p-values.
* **Validity checks per run:** task accounting adds up, message log balanced, no exception. Invalid/errored runs are
  kept in the raw files and counted in the metadata.
* **Hardware/software.** Recorded in `experiments/results/metadata/*.json`. Runtimes were measured on a small shared
  Linux sandbox (see metadata) and must not be compared with numbers from other machines.

## Threats to validity
*Internal:* planner runtimes include Python interpreter noise; CBS limits (node/time) turn some runs into fallbacks,
which are counted. *External:* one family of grid warehouses, synthetic tasks, unit-speed abstraction.
*Construct:* completion rate alone hides time, energy and compute cost; collisions alone hide waiting. Hence several
metrics per question. *Reproducibility:* simulated metrics are exactly reproducible from config + seed; wall-clock
metrics are not.
