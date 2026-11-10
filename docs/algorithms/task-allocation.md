# Task allocation

For \(N\) robots and \(M\) tasks the cost model builds
\[ c_{ij} = w_d D_{ij} + w_t T_{ij} + w_e E_{ij} + w_l L_i - w_p P_j \]
with \(D\) path distance (BFS), \(T\) estimated time, \(E\) estimated energy (load-dependent), \(L_i\) the robot's
accumulated busy time, \(P_j\) task priority. Weights are configuration, not "optimal" values.

**Feasibility is a hard mask**, never a penalty: missing capability, payload above capacity, insufficient battery
(job energy + energy to the nearest charger + reserve), unreachable cell, or a pair the robot already rejected give
\(c_{ij} = \infty\). Solvers see the same non-negative matrix: feasible entries shifted by the minimum, infeasible
entries set to \(\mathrm{BIG} = k\,(\max-\min) + 1\) with \(k = \min(N, M)\), so any solution with fewer infeasible
pairs is cheaper - the solvers first maximise the number of feasible assignments, then minimise cost; infeasible
pairs are dropped from the result and validated (`validate_assignment`).

Allocation runs in batches whenever idle robots and pending tasks exist (rolling horizon). **Reassignment** avoids
oscillation with a minimum interval since assignment, a switching cost, a minimum relative improvement and
commitment (no stealing once a robot has reached the pickup); robot loss, connection loss and low battery force it.
**Workload balance** is reported as std, max, min and coefficient of variation of per-robot busy time.
