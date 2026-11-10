# SwarmForge

**Multi-Robot Coordination, Task Allocation and Autonomous Fleet Simulation Platform**
TECHNICAL SYSTEM REPORT - VERSION 0.1 (development snapshot)

## Table of contents
1. Abstract - 2. Introduction - 3. Problem definition - 4. System requirements - 5. System architecture - 6. Mathematical models -
7. Algorithm design - 8. Implementation - 9. Testing and validation - 10. Experimental methodology - 11. Results and discussion -
12. Limitations - 13. Conclusion - 14. Future work - 15. References - 16. Appendices

## 1. Abstract

SwarmForge is a deterministic multi-robot warehouse simulator and experiment platform. It implements, from scratch, Hungarian and Auction
task allocation, Dijkstra / A* / space-time A* / prioritised cooperative planning / Conflict-Based Search, grid-level collision arbitration, a
continuous ORCA implementation, heterogeneous robots with an energy and charging model, and a latency/loss/heartbeat communication layer, together
with C++20 kinematics kernels, a FastAPI service, a React dashboard, a ROS 2 package and generated Gazebo assets. Eight seeded experiments (588 runs in the
reduced "quick" profile) show, among other things, that optimal batch assignment is cheap relative to its benefit over greedy assignment (up to 29 % lower cost), that
uncoordinated planning needs execution-time avoidance but that wait-only avoidance livelocks, that CBS and prioritised planning differ little in the engine's incremental setting,
that latencies below the decision step are absorbed and an acknowledged-assignment protocol makes 10 % loss survivable, and that charging, not energy-aware allocation alone, determines
completion for energy-limited fleets. The experiments also exposed a real protocol bug (a stale acknowledgement confirming a newer assignment), which was fixed and covered by a regression test.

## 2. Introduction

Fleet-scale warehouse robotics couples four problems that are usually studied separately: who does which task (allocation), which route each robot takes without
conflicts (multi-agent path finding), how robots avoid each other while executing (coordination), and how all of it behaves when information is stale or robots fail (communication and
resilience). SwarmForge makes these couplings explicit and measurable: every subsystem is replaceable behind a small interface, and every claim is backed by a seeded, recorded run.

## 3. Problem definition

* **Robots** \(r_i\): profile (max speed, acceleration, payload capacity, battery capacity, energy per metre, capability set), cell, battery level, at most one task.
* **Tasks** \(\tau_j\): pickup cell, destination cell, priority, payload, required capabilities, creation time, deadline; lifecycle PENDING -> ASSIGNED -> IN_PROGRESS -> COMPLETED
  (or FAILED/CANCELLED, or back to PENDING).
* **Environment:** 4-connected grid with static shelves, dynamic blockages, pickup/delivery/spawn/charging zones; discrete time with fixed step.
* **Constraints:** capability and payload feasibility, battery sufficiency incl. return to a charger and reserve, no two robots in one cell at one step, no swapping, one cell per plan step.
* **Objectives:** minimise a weighted cost of distance, time, energy, workload imbalance and priority (allocation); minimise path length (planning); maximise completed tasks and throughput subject to safety (system level).
* **Assumptions:** centralised fleet manager with delayed/lossy knowledge; unit-speed abstraction; known map; instantaneous loading with a fixed dwell.

## 4. System requirements

| ID | Requirement | Acceptance criterion | Verified by |
|---|---|---|---|
| FR-01 | Register robots | unique IDs, validated profiles | `test_robot.py` |
| FR-02 | Create tasks | valid lifecycle and timestamps | `test_task.py`, integration timestamp test |
| FR-03 | Allocate tasks | feasible, validated assignment | allocation tests |
| FR-04 | Plan paths | valid, conflict-free (coordinated planners) | planning + integration tests |
| FR-05 | Run simulation | deterministic stepping | `test_determinism...`, golden tests |
| FR-06 | Collect metrics | validated records | experiment runner `valid` flag |
| NFR-01 | Reproducibility | same seed and config -> identical simulated metrics | determinism and runner tests |
| NFR-02 | Extensibility | new algorithm = protocol implementation | `core/interfaces.py` |
| NFR-03 | Core independence | no ROS/Gazebo/web imports in `src/swarmforge` | ADR-0004 |

Performance and reliability requirements are stated qualitatively only: no real-time claim is made (see section 12).

## 5. System architecture

See `docs/architecture/`. In short: Python core (`src/swarmforge`) with ordered tick phases; C++20 kernels (`cpp/`) behind a C ABI; consumers (CLI, experiment runner, FastAPI/WebSocket
+ React, ROS 2 bridge + Gazebo). Mode A (abstract grid) is used for all benchmarks; Mode B (Gazebo) is for visual/physical inspection and is not expected to reproduce Mode A numbers.

## 6. Mathematical models

* Allocation cost \(c_{ij} = w_dD_{ij}+w_tT_{ij}+w_eE_{ij}+w_lL_i-w_pP_j\), infeasible pairs \(=\infty\); objective \(\min\sum x_{ij}c_{ij}\), \(x_{ij}\in\{0,1\}\).
* Planning: A* \(f=g+h\), \(h\) = Manhattan (single-agent) or exact BFS distance (space-time); route = sequence \((x,y,t)\); vertex constraint \((cell,t)\), edge constraint \((a,b,t)\).
* Collision: \(d_{ij}=\lVert p_i-p_j\rVert\); actual \(d<r_i+r_j\); violation \(d<r_i+r_j+m\); potential: constant-velocity closest approach within 1 s.
* Kinematics: \(\dot x=v\cos\theta,\ \dot y=v\sin\theta,\ \dot\theta=\omega\); wheels \(v=\tfrac r2(\omega_R+\omega_L)\), \(\omega=\tfrac rL(\omega_R-\omega_L)\).
* Energy: \(E=e_d\,D\,(1+0.5\,m/m_{max})+P_{idle}\Delta t\) (simplified, uncalibrated).
* Communication: \(t_{delivery}=t_{created}+\delta\); loss Bernoulli(p); expiry after TTL; unreachable if silent longer than the state timeout.
* Metrics: \(R_c=N_{completed}/N_{created}\), \(T_{avg}=\frac1{N_c}\sum(t^{complete}_i-t^{creation}_i)\), \(T_{execution}=t^{complete}-t^{start}\), throughput \(=N_{completed}/T_{observation}\).

## 7. Algorithm design

Each algorithm has a page in `docs/algorithms/` covering problem, input/output, formulation, procedure, complexity and limitations: Hungarian \(O(n^2m)\); Auction (epsilon-scaling, gap bound \(k\varepsilon\));
A*/Dijkstra \(O(E\log V)\); space-time A* over \(V\times T\) states; prioritised planning (incomplete); CBS (exponential worst case in the number of conflicts); wait-for-graph cycle detection (Tarjan SCC);
ORCA (incremental 2-D LP).

## 8. Implementation

Python 3.12, dataclasses with validation, `typing.Protocol` extension points, NumPy for vector work (collision monitor, cost matrices), tuples for grid cells on hot paths. The C++ kernels expose a C ABI used through
`ctypes` and an optional pybind11 module; scikit-build-core drives CMake. Configuration is a typed hierarchy with YAML inheritance and dotted overrides. Communication runs through an in-process bus with logged outcomes.
The engine is deliberately single-threaded and deterministic; the API layer owns threading.

## 9. Testing and validation

165 Python tests in `tests/` (executed here with a minimal pytest stand-in; the 3 Hypothesis tests were not executed) plus 6 API-service and 4 ROS-bridge tests run separately: unit (Hungarian vs brute force and SciPy; auction within its bound; A* vs Dijkstra on random maps; CBS vs prioritised; ORCA scenarios; kinematics vs C++; message accounting), integration (determinism, failures, packet loss,
capability, energy, dynamic obstacles, invariants each step), system (CLI, experiment outputs and metadata, runnable examples), regression (golden metrics for five scenarios), property tests (Hypothesis, skipped when it is not installed), plus C++ tests
(16 checks in four executables), API-service and ROS-bridge tests. Test coverage percentages were **not measured** in the authoring environment and are therefore not reported. Validation of simulation outputs: per-run accounting checks, balanced message logs, safety invariants.
Not executed in the authoring environment: ruff, mypy, pytest itself (a minimal stand-in runner was used), CMake builds, FastAPI, ROS 2, Gazebo, the React build.

## 10. Experimental methodology

See `docs/research/experimental-methodology.md`: seeded and paired scenarios, 3-5 seeds in the executed quick profile (10 in the full profile), mean/SD/95 % CI/IQR, paired t-test, Wilcoxon, Cohen's d_z, metadata capture.

## 11. Results and discussion

The full analysis is in [`benchmark-report.md`](benchmark-report.md); each experiment has a page in `docs/experiments/`. Three results deserve emphasis because they are easy to get wrong:

1. **Collision counts alone mislead.** Wait-only avoidance had zero collisions but only 80-83 % completion; reciprocal sidestepping achieved zero collisions and full completion.
2. **Grid-conflict-free is not clearance-safe.** Coordinated plans still produced tens to over a hundred safety-distance violations per run because robots cut corners between adjacent cells.
3. **A faster kernel is not a faster system.** The C++ kinematics kernel is ~28x faster than Python in batch and slower per call, and kinematics is not on the simulator's hot path (cost-matrix construction 40 %, collision monitor 23 %, planning 20 % of a profiled run).

## 12. Limitations

See `docs/research/limitations.md` (grid and unit-speed abstraction, simplified energy and network models, incremental CBS, incomplete prioritised planning, ORCA not integrated into the grid engine, unexecuted integration layers, few seeds).

## 13. Conclusion

SwarmForge delivers a complete, tested, reproducible core and experiment framework, plus integration layers that are written but not yet executed against their runtimes. The experiments are consistent with expectations from the literature
(optimal assignment beats greedy; independent planning needs coordination; robot failures cost far more than a lossy network once assignments are acknowledged) and produced concrete findings about the modelling choices themselves (plan-step quantisation of latency; plan-step set by the slowest robot).

## 14. Future work

Full-profile runs; fleet sizes up to 50; ORCA/continuous Mode B integration; per-robot speeds in the planner; decentralised auctions; ROS 2 services/actions; learning-based allocation; hardware-in-the-loop.

## 15. References

* H. W. Kuhn, "The Hungarian method for the assignment problem", Naval Research Logistics, 1955.
* D. P. Bertsekas, "The auction algorithm: a distributed relaxation method for the assignment problem", Annals of Operations Research, 1988.
* P. Hart, N. Nilsson, B. Raphael, "A formal basis for the heuristic determination of minimum cost paths", 1968.
* D. Silver, "Cooperative pathfinding", AIIDE 2005.
* G. Sharon, R. Stern, A. Felner, N. Sturtevant, "Conflict-based search for optimal multi-agent pathfinding", Artificial Intelligence, 2015.
* J. van den Berg, S. J. Guy, M. Lin, D. Manocha, "Reciprocal n-body collision avoidance", ISRR 2011 (ORCA).
* R. E. Tarjan, "Depth-first search and linear graph algorithms", SIAM J. Computing, 1972.
* ROS 2 Jazzy and Gazebo Harmonic documentation (installation compatibility for Ubuntu 24.04).

## 16. Appendices

A. Configuration reference: `docs/user-guide/configuration.md`. B. Experiment specifications: `experiments/scenarios/`. C. Raw results and metadata: `experiments/results/`. D. Benchmarks and profile: `benchmarks/`
(`kinematics_results.json`, `profile_results.json`). E. ADRs: `docs/design-decisions/`.
