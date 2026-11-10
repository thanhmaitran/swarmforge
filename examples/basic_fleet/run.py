"""Goal: run a small fleet to completion and print the headline metrics.

Command:  python examples/basic_fleet/run.py
Algorithms: Hungarian allocation, cooperative A* planning, priority-based move arbitration.
Validation: tests/system/test_examples.py checks the printed completion rate and collision count.
"""

from swarmforge.config import load_config
from swarmforge.simulation.engine import SimulationEngine

cfg = load_config("warehouse_small", {"fleet.robot_count": 5, "tasks.count": 15, "simulation.seed": 42})
engine = SimulationEngine(cfg)
s = engine.run()
print(f"completed {s['completed_tasks']}/{s['created_tasks']} tasks in {s['simulation_time']:.1f} s")
print(f"collisions={s['collision_count']} distance={s['total_distance']:.0f} m termination={s['termination_reason']}")
print("final map:\n" + engine.warehouse.render_ascii({r.cell: "R" for r in engine.fleet.robots}))
