# Component architecture

```text
Scenario(config, seed) --> Warehouse, Tasks, Fleet, Events
SimulationEngine
  |- FleetManager ........ registry, fleet-side assignments, unreachable set, in-flight assignments
  |- CommunicationManager  MessageBus + StateCache + HeartbeatMonitor
  |- AllocationManager .... CostModel -> {Hungarian | Auction | Greedy}, ReassignmentPolicy
  |- PlanningManager ...... {IndependentPlanner | CooperativePlanner | CBSPlanner (+ cooperative fallback)}
  |- CoordinationManager .. resolve_moves(none|basic|reciprocal), DeadlockDetector, CongestionManager
  |- ResourceManager ...... charging stations + reservations
  |- CollisionMonitor ..... actual / safety-distance / potential episodes
  '- MetricsCollector
```

Two knowledge levels are modelled on purpose:

* **Ground truth** - `Robot` objects (positions, batteries, tasks). Only the engine and metrics see it.
* **Fleet belief** - `StateCache` filled by delayed/lossy messages, plus the heartbeat monitor. Allocation reads
  *believed* positions and batteries; robots only start a task when the `ASSIGN` message reaches them.

Extension points are `typing.Protocol`s in `swarmforge.core.interfaces`: `Allocator`, `MultiAgentPlanner`,
`MotionModel`. A new allocator needs `name` and `allocate(cost_matrix) -> AllocationResult`.
