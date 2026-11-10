# System overview

```text
                +--------------------------- experiments/ ---------------------------+
                |  runner -> raw CSV/JSONL -> aggregate (mean, SD, CI) -> tables/figs |
                +----------------------------------+--------------------------------+
                                                   |
 React dashboard <-- WebSocket/REST -- FastAPI --> SimulationEngine (core, pure Python)
                                                   |   ^
 ROS 2 bridge  <------- snapshots / new tasks -----+   |   C++ kernels (ctypes / pybind11)
 Gazebo (Mode B)  <-- /swarmforge/robot_NN/pose         |   differential-drive kinematics
```

**Mode A - algorithm simulation:** the core engine moves abstract robots on a grid; used for all benchmarks.
**Mode B - physics simulation:** robots are Gazebo models driven through ROS 2; results are *not* expected to match
Mode A (different resolution and dynamics).

The core never imports ROS, Gazebo, FastAPI or the dashboard (ADR-0004). Layers above it consume `snapshot()`
and call `add_task()`.

## Packages (`src/swarmforge`)

| Package | Responsibility |
|---|---|
| `core` | value types, enums, exceptions, clock, events, protocols |
| `agents` | robot profiles, robot state machine and energy bookkeeping |
| `environment` | warehouse grid, tasks (lifecycle), task generator, map loading |
| `allocation` | cost model, Hungarian, Auction, greedy, reassignment policy, workload statistics |
| `planning` | grid graph + distance oracle, Dijkstra, A*, space-time A*, cooperative, CBS, deadlock graph |
| `coordination` | collision monitor, move arbitration, velocity obstacles, ORCA, congestion |
| `motion` | differential-drive kinematics (Python reference), velocity limiter, native bridge |
| `fleet` | robot registry, fleet construction and fleet-side bookkeeping |
| `communication` | message bus (latency/loss/expiry), state cache, heartbeats, manager |
| `resources` | battery, energy model, charging stations, reservations |
| `simulation` | scenario builder, engine, scheduler, event queue, lifecycle |
| `metrics`, `experiments`, `visualization` | measurements, experiment framework, rendering |
