# Collision avoidance and safety

**Three distinct notions** (`CollisionMonitor`, counted as *episodes*, with \(d_{ij}=\lVert p_i-p_j\rVert\)):
actual collision \(d < r_i + r_j\); safety-distance violation \(d < r_i + r_j + m\) (not overlapping); potential
collision: constant-velocity extrapolation over 1 s brings the pair within \(r_i + r_j\) although currently beyond
the margin.

**Execution-time arbitration (`coordination.avoidance`)**

| Mode | Behaviour |
|---|---|
| `none` | everybody follows its plan; collisions are only observed |
| `basic` | a robot waits if the target cell is occupied/claimed or the move would swap with another; priority = task priority, then ID |
| `reciprocal` | as `basic`, but after waiting a blocked lower-priority robot *sidesteps* into a free neighbour so that both robots of a head-on pair help resolve it |

!!! note "Naming"
    `reciprocal` is **not** ORCA. A full 2-D ORCA implementation (half-planes + incremental LP) lives in
    `coordination/orca.py` and is verified in continuous space (head-on, crossing, 8-agent circle); it is not wired into
    the grid engine. Velocity-obstacle geometry and a sampling VO selector are in `velocity_obstacles.py`.

**Invariants** (`check_invariants`, run each decision step in tests): robots stay inside the map and outside static
obstacles, speed never exceeds `max_speed`, batteries stay in range, no task is owned by two robots, capability
constraints hold, an unavailable robot does not move. Maximum acceleration is enforced by `VelocityLimiter` in the
kinematic layer; the grid abstraction itself moves at constant speed per step.

Simulation results say nothing about the safety of physical robots.
