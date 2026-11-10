# SwarmForge Benchmark Report

*Every number in this report comes from a recorded run: raw records in `experiments/results/raw/`, metadata in
`experiments/results/metadata/`, produced by `python experiments/runners/batch_runner.py --profile quick` and
`python experiments/analysis/generate_report_assets.py`. Nothing was typed in by hand except the prose that interprets it.*

## 1. Executive summary

* **Allocation.** Hungarian and Auction reached identical total cost in all 270 allocation runs (auction always converged,
  gap bound 0.001 per pair). Hungarian was faster on the simulated matrices (median 0.41 ms vs 7.4 ms at 5 robots x 100 tasks,
  7.0 ms vs 8.3 ms at 25 x 100); on dense square random matrices the auction overtakes it from 50 x 50 (1.8 ms vs 2.3 ms; 4.1 ms vs 9.4 ms at 100 x 100).
  The greedy baseline costs up to 29 % more (0.1 % when robots outnumber tasks; paired mean +252 cost units over 90 pairs, d_z = 1.33).
* **Planning.** Independent A* is optimal per robot but produces on average 0.6-9.0 conflicts per instance (5-10 robots);
  prioritised cooperative planning and CBS produce none. CBS's solutions were slightly shorter (sum-of-costs ratio to the single-agent lower bound
  1.007-1.008 vs 1.010-1.024) at higher cost; with 10 robots at 25 % obstacle density CBS solved only 80 % of instances within 2000 nodes / 3 s.
* **Collision avoidance.** Without avoidance, uncoordinated planning collides (56 and 94 collision episodes per run at 8 and 16 robots);
  wait-only avoidance removes collisions but livelocks (80-83 % completion, thousands of waits); reciprocal sidestepping removes
  collisions *and* completes everything (100 %), at 202-273 waits per run; coordinated planning needs no waits at all.
  Grid-conflict-free plans still produce safety-distance violations (61-123 per run).
* **Scalability.** Throughput grows almost linearly with fleet size (0.045 -> 0.076 -> 0.209 tasks/s for 5 -> 10 -> 25 robots); CBS
  and A* gave identical *simulated* outcomes in this workload, CBS cost roughly 4-5x the planning runtime.
* **Dynamic environment, communication, heterogeneity, energy.** Robot failures cost +28.6 s (13 %); inserted/temporary obstacles
  were absorbed (+3.6 s, n.s.); latencies up to 1 s are absorbed by the 1 s plan step (+1 s), 2 s latency costs +2 s and 10 % loss +2.1 s (paired, n = 40),
  while failures dominate (+28 s); capability-unaware allocation wasted ~60 assignment rounds per run; energy-aware allocation avoided all battery
  depletions (0 vs 5 dead robots) but only charging reached 100 % completion.
* **Performance engineering.** The C++ kinematics kernel is ~28x faster than the Python loop when called in batch and *slower* (0.3x) when
  called per step through ctypes; the simulator's hot spots are cost-matrix construction (40 %), the collision monitor (23 %) and planning (20 %) -
  none of which are kinematics.

## 2. Experimental environment

| | |
|---|---|
| Code version | commit `ca4bcfb1` (clean working tree) recorded in every metadata file (`git_commit`, `git_dirty`) |
| Profile | **quick**: 3-5 seeds per cell and reduced grids (exact grids in `experiments/scenarios/*.yaml`); the 10-seed *full* profile was **not** run |
| Runs | 270 + 120 + 40 + 18 + 25 + 80 + 20 + 15 = 588, 0 errors, 0 invalid (task accounting and message-log balance checked per run) |

## 3. Hardware and software

Linux 6.18 (x86_64), 1 vCPU shared sandbox, Python 3.12.3, NumPy/SciPy/pandas, g++ 13.3.0. Simulated metrics are exactly reproducible
anywhere; **runtimes (ms) are specific to this machine.**

## 4. Benchmark methodology

Seeded scenarios, paired comparison on identical seeds, mean / SD / Student-t 95 % CI per cell (IQR and median in `aggregated/*.csv`),
paired t-test + Wilcoxon + Cohen's d_z for selected contrasts ([paired table](tables/paired_comparisons.md)). With 3-5 seeds the CIs are wide
(and can extend below zero for skewed non-negative data such as runtimes - use the medians in the aggregated files for those); with n = 5 the
smallest possible two-sided Wilcoxon p-value is 0.0625. Treat the quick-profile results as indicative.

## 5. Fleet scalability  ([details](../docs/experiments/experiment-01-scalability.md))

| robots | planner | completion | throughput (tasks/s) | avg completion time (s) | planning runtime (ms/run) | CBS fallbacks/run |
|---|---|---|---|---|---|---|
| 5 | A* (coop) | 100 % | 0.045 | 426.6 | 66.0 | - |
| 5 | CBS | 100 % | 0.045 | 427.1 | 262.7 | 0.33 |
| 10 | A* (coop) | 100 % | 0.076 | 229.9 | 99.3 | - |
| 10 | CBS | 100 % | 0.076 | 229.7 | 488.5 | 0.67 |
| 25 | A* (coop) | 100 % | 0.209 | 112.6 | 190.0 | - |
| 25 | CBS | 100 % | 0.209 | 112.5 | 856.2 | 1.33 |

40 tasks, `warehouse_medium`, 3 seeds. Fleet sizes 50 and the 100-task workload of the full profile were not run.
Planning cost grows with fleet size (more robots -> larger reservation tables and more replans); CBS adds roughly 4-5x (paired mean +417 ms per run, d_z = 1.27). In the engine CBS only plans the
small batch of robots needing a route at a decision step (others are fixed), which is why it rarely differs from prioritised planning here.

## 6. Task allocation comparison  ([details](../docs/experiments/experiment-02-allocation.md))

Assignment cost and runtime for 5/10/25 robots x 20/50/100 tasks, homogeneous and heterogeneous fleets, 5 seeds x 2 fleet types (n = 10 per cell).

| algorithm | 5 x 100 runtime (ms) | 10 x 100 | 25 x 100 | cost gap vs Hungarian |
|---|---|---|---|---|
| Hungarian | 0.41 | 1.32 | 7.01 | 0 |
| Auction | 7.36 | 7.87 | 8.34 | 0 (converged in every run, median 1364 bids) |
| Greedy | 0.04 | 0.04 | 0.14 | +29 % / +25 % / +17 % (5/10/25 robots, 100 tasks) |

In the heterogeneous fleet (62 % of robot-task pairs feasible) all algorithms assigned the maximum number of feasible pairs (100 % assignment success, 43.9 tasks left unassigned on average for lack of robots).
Dense square matrices (`benchmarks/allocation/bench_allocation.py`, median of 5): Hungarian 0.09 / 0.41 / 2.33 / 9.42 ms and Auction 0.31 / 0.76 / 1.78 / 4.10 ms for 10 / 25 / 50 / 100. Runtimes vary by tens of percent between repetitions of the same experiment on this shared machine; orderings, not absolute values, are the finding.

## 7. Path planning comparison  ([details](../docs/experiments/experiment-03-planning.md))

Random MAPF instances on a 20 x 20 map, 5 seeds x 2 densities (n = 10 per row).

| planner | robots | success | conflicts/instance | sum-of-costs / single-agent bound | runtime (ms, median, 25 % density, 10 robots) |
|---|---|---|---|---|---|
| Dijkstra | 10 | 100 % | 8.0 (25 %) | 1.000 | 2.6 |
| A* | 10 | 100 % | 9.0 (25 %) | 1.000 | 0.7 |
| Prioritised cooperative | 10 | 100 % | 0 | 1.024 | 5.5 |
| CBS | 10 | 80 % at 25 % density | 0 | 1.008 | 42.3 |

A* expanded 797 fewer nodes than Dijkstra per instance on average (paired, d_z = -1.37) at identical cost. Single-agent search and multi-agent search solve different
problems; the "conflicts" column is what the single-agent plans would have caused if executed together. The 20 % failures of CBS are node/time-limit exhaustion (2000 nodes, 3 s), not proofs of infeasibility.

## 8. Collision avoidance  ([details](../docs/experiments/experiment-04-collision.md))

`warehouse_small`, 40 tasks, 8 and 16 robots, 5 seeds.

| strategy | robots | completion | collisions | safety violations | waits | deadlocks | sim. time (s) |
|---|---|---|---|---|---|---|---|
| independent, none | 8 / 16 | 100 % | 56 / 94 | 147 / 244 | 0 | 0 | 254 / 154 |
| independent, basic (wait) | 8 / 16 | 80 % / 82.5 % | 0 | 48 / 80 | 3121 / 4892 | 0.8 / 0.2 | 777 / 550 (some runs hit the time limit) |
| independent, reciprocal | 8 / 16 | 100 % | 0 | 70 / 113 | 202 / 273 | 0 | 317 / 183 |
| cooperative (A*), basic | 8 / 16 | 100 % | 0 | 61 / 123 | 0 | 0 | 261 / 155 |

Collision counts alone would rank "basic" as perfect; its completion rate shows it is not (head-on pairs wait for each other, replan around the blocker and repeat).
Paired over seeds: reciprocal vs basic -3769 waits (p = 0.015 / Wilcoxon 0.002, d_z = -0.94); none vs basic +75 collisions (d_z = 3.5).

## 9. Dynamic environment adaptation  ([details](../docs/experiments/experiment-05-dynamic-environment.md))

10 robots, 40 tasks, 5 seeds: static 213.7 s; obstacle insertion (8 permanent) 217.3 s (+3.6 s, p = 0.15) with 7.8 replans; temporary blockage 217.5 s (8.0 replans);
2 robot failures 242.3 s (+28.6 s, d_z = 5.7, 2.0 replans, 1.8 reassignments); Poisson arrivals are arrival-limited (369 s total, but 42.6 s mean completion time vs 115.9 s for batch arrival).
All scenarios completed 100 % of tasks.

## 10. Communication constraints  ([details](../docs/experiments/experiment-06-communication.md))

Latency 0 / 500 / 1000 / 2000 ms x loss 0 / 10 % x random failures 0 / 2, 5 seeds (80 runs), state timeout 2 s. Mean simulated time without failures: 213.7 s at 0 ms; 214.7 s at 500 ms **and** 1000 ms (identical: any latency up to
one 1 s plan step costs exactly one decision step); 215.7 s at 2000 ms; with 10 % loss 216.3-216.9 s. With two failures: 242.3 s (no latency/loss) to 245.9 s (2000 ms + 10 % loss). Paired over seeds, 10 % loss adds +2.1 s (p = 0.004, d_z = 0.48, 40 pairs).
Task completion was 100 % in every run; heartbeat timeouts of healthy robots ("unreachable events") occurred 0.2 times per run at 2000 ms + 10 % loss and were recovered by retransmission/reassignment. With this acknowledged-assignment protocol the fleet
tolerates these stress levels at a cost of seconds, and robot failures (+28 s) matter far more than the network. The 50/100/250 ms levels of the full profile were not run (they would be absorbed like 500 ms).

!!! note "A bug this experiment found"
    An earlier run of this experiment showed two runs (2000 ms, 10 % loss, seed 42) that never finished: a *stale* acknowledgement of a revoked assignment confirmed a newer assignment of the same task to the same robot, so the
    dropped `ASSIGN` was never retransmitted. Acknowledgements now echo an `assign_id`; the fix and a regression test are in the repository, and all numbers in this report come from runs of the fixed code.

## 11. Heterogeneous fleet  ([details](../docs/experiments/experiment-07-heterogeneous-fleet.md))

| setup | completion | unfinished | rejected assignments/run | workload CV | mean execution time (s) |
|---|---|---|---|---|---|
| homogeneous fleet, standard tasks | 100 % | 0 | 0 | 0.139 | 28.7 |
| homogeneous fleet, mixed tasks | 62.5 % | 15 | 0 | 0.175 | 29.2 |
| heterogeneous, capability-aware | 100 % | 0 | 0 | 0.154 | 43.1 |
| heterogeneous, capability-unaware | 100 % | 0 | 59.8 | 0.154 | 42.9 |

Capability awareness is necessary for feasibility *per assignment* but the retry-with-blacklist baseline still finishes (simulated time differs by -12.3 s in favour of awareness, p = 0.25, n = 5). Heavy/fast tasks lengthen execution (heavy
robots set the plan step to 1.5 s); a homogeneous fleet cannot execute heavy tasks at all.

## 12. Energy-aware coordination  ([details](../docs/experiments/experiment-08-energy.md))

| strategy | completion | unfinished | battery depletions (of 5 robots) | energy/task | charging utilisation |
|---|---|---|---|---|---|
| distance only, no charging | 66.7 % | 20 | 5 | 50.1 | 0 |
| energy-aware, no charging | 58.3 % | 25 | 0 | 50.6 | 0 |
| energy-aware + charging | 100 % | 0 | 0 | 53.9 | 4.3 % |

Without charging, energy awareness avoids stranding robots but leaves reserve energy unused (-8.3 points completion); with charging all 60 tasks complete at +8 % energy per task (travel to chargers).
Dead robots block their cells, which is part of why the distance-only variant ends with five immobile robots.

## 13. Statistical analysis

See [`tables/paired_comparisons.md`](tables/paired_comparisons.md). Large effects (d_z > 1) with consistent sign: Hungarian faster than Auction on the simulated matrices, greedy costlier than Hungarian, CBS slower than A*,
A* expanding fewer nodes than Dijkstra, no-avoidance collisions, robot failures lengthening runs. Contrasts with p between 0.05 and 0.15 (CBS vs cooperative cost, reciprocal vs basic completion, obstacle insertion, 500 ms latency) are
suggestive only. No multiple-comparison correction was applied.

## 14. Threats to validity

*Internal:* runtimes were measured on a shared single-vCPU machine; CBS limits turn instances into failures/fallbacks (counted). Event times are quantised to the plan step. *External:* one warehouse family, synthetic tasks, unit-speed
abstraction (all robots move at the slowest robot's speed), simplified energy and network models. *Construct:* completion rate, collisions and waiting each hide part of the picture (see section 8); "safety violations" measure
continuous clearance, not grid conflicts. *Reproducibility:* simulated outputs are deterministic given configuration and seed (tested); wall-clock outputs are not.

## 15. Conclusions

For small-to-medium fleets in this simulator: optimal batch assignment is cheap, so there is little reason to use the greedy baseline; prioritised cooperative planning is almost as good as CBS at a fraction of the cost and CBS is best kept for
small batches; execution-time avoidance cannot replace coordinated planning, and the *type* of avoidance (wait vs sidestep) matters more than whether there is one; charging is the decisive factor for energy-limited fleets; latency below the decision step is
cheap (+1 s up to the plan step, +2 s at 2 s) and the acknowledged-assignment protocol makes loss survivable; robot failures dominate the cost of an unreliable fleet. Verifying these conclusions with the full 10-seed profile, larger fleets (50 robots) and the 50-250 ms latency levels is the first item of future work.
