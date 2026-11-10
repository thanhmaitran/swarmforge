# Examples

Every example is a self-contained script (`python examples/<folder>/<script>.py`), prints its result, and is
executed by `tests/system/test_examples.py`, so they cannot silently rot. Run them from the repository root
after `pip install -e .` (or with `PYTHONPATH=src`).

| Example | Goal | Expected output |
|---|---|---|
| `basic_fleet/run.py` | Run a 5-robot fleet end to end | all tasks complete, 0 collisions |
| `task_allocation/hungarian_demo.py` | Optimal assignment on a tiny cost matrix | total cost 4.0 |
| `task_allocation/auction_demo.py` | Auction vs Hungarian on random matrices | auction within its stated bound |
| `multi_robot_planning/astar_demo.py` | A* vs Dijkstra on a map with a wall | equal cost, fewer expansions for A* |
| `multi_robot_planning/cbs_demo.py` | Head-on swap that only CBS solves | independent planning has a conflict, CBS none |
| `multi_robot_planning/orca_demo.py` | Continuous reciprocal avoidance | minimum separation >= 2r |
| `dynamic_environment/dynamic_obstacle_demo.py` | Aisle blocked mid-run | replans, all tasks still complete |
| `heterogeneous_fleet/capability_aware_demo.py` | Capability-aware vs unaware allocation | unaware wastes assignments |
| `communication_constraints/delayed_communication_demo.py` | Latency and packet loss | later task starts, balanced message log |
| `energy_aware/energy_allocation_demo.py` | Energy-aware allocation with charging | no battery depletions |
