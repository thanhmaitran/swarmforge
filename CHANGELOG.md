# Changelog

All notable changes are documented here. The project follows [Semantic Versioning](https://semver.org/)
and the [Keep a Changelog](https://keepachangelog.com/) format.

## [0.1.0] - Unreleased

Initial development snapshot covering the complete planned architecture.

### Added
- Core simulation engine: deterministic fixed-step clock, ordered tick phases, event queue, lifecycle.
- Task allocation: Hungarian (shortest augmenting path), Auction (epsilon-scaling), greedy baseline,
  capability/battery feasibility, reassignment policy, workload statistics.
- Planning: Dijkstra, A*, space-time A*, prioritised cooperative planning with reservation table,
  Conflict-Based Search (vertex + edge conflicts), wait-for-graph deadlock detection.
- Coordination: three distinct safety metrics, priority/reciprocal move arbitration, velocity obstacles, ORCA.
- C++20 kinematics kernels with a ctypes bridge and optional pybind11 module.
- Heterogeneous fleet, energy model, charging, shared-resource reservations.
- Communication: latency, jitter, packet loss, expiry, state cache, heartbeats, acknowledged assignments.
- Experiment framework (8 experiments), statistics, figures, metadata capture.
- FastAPI service + WebSocket stream, React dashboard, ROS 2 package, generated Gazebo assets.
- Documentation (architecture, algorithms, ADRs, research notes), CI workflows, Docker files.

### Fixed
- Assignment ACKs now echo an `assign_id`; a stale ACK from a revoked assignment could previously confirm a newer
  assignment of the same task to the same robot and leave the task `ASSIGNED` forever (found by the communication
  experiment at 2000 ms latency + 10 % loss; regression test `test_stale_ack_never_confirms_a_newer_assignment`).
