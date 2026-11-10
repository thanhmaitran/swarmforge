# ADR-0002: Grid-based abstract simulation

## Status
Accepted

## Context
Multi-agent path finding, reservation tables and CBS are defined on discrete graphs. Continuous physics would make
algorithmic comparisons depend on controller tuning.

## Decision
Robots move on a 4-connected grid, one cell per plan step ("unit-speed MAPF abstraction"). `plan_step` defaults to
the time the *slowest* robot needs for one cell, so that the invariant "speed <= max_speed" holds for every profile.
Continuous positions are obtained by interpolation for metrics, rendering and the ROS bridge.

## Consequences
Positive: exact planner semantics, reproducibility, speed. Trade-offs: **speed heterogeneity does not change how fast
a robot moves** in Mode A (faster robots are not faster); heterogeneity acts through capability, payload, battery and
energy cost. Grid-conflict-free plans can still violate continuous clearance (diagonal corner cutting) - which the
`safety_violations` metric exposes. Mode B (Gazebo) is the place for continuous dynamics.
